import uuid
from datetime import datetime, timezone

import structlog

from app.config.settings import get_settings
from app.domains.ingestion.chunkers.base import IChunker
from app.domains.ingestion.embedders.base import IEmbedder
from app.domains.ingestion.loaders.base import IDocumentLoader, SourceInput
from app.domains.ingestion.schemas import SourceOut
from app.domains.ingestion.validators import sniff_and_verify, validate_file_size, validate_url
from app.infrastructure.cache.cache_keys import embedding_key, source_set_hash
from app.infrastructure.cache.redis_adapter import RedisCacheAdapter
from app.infrastructure.vectorstore.base import IVectorStore, VectorRecord
from app.shared.exceptions import IngestionError, NotFoundError

log = structlog.get_logger()


class IngestionService:
    def __init__(
        self,
        loaders: dict[str, IDocumentLoader],
        chunker_factory,
        embedder: IEmbedder,
        vector_store: IVectorStore,
        cache: RedisCacheAdapter,
        settings,
    ):
        self._loaders = loaders
        self._chunker_factory = chunker_factory
        self._embedder = embedder
        self._vs = vector_store
        self._cache = cache
        self._settings = settings
        self._sources: dict[str, SourceOut] = {}

    async def ingest_file(self, filename: str, content: bytes, kind: str | None = None) -> SourceOut:
        kind = kind or self._infer_kind(filename)
        validate_file_size(content, kind)
        sniff_and_verify(content, kind)
        source_id = uuid.uuid4().hex
        source = SourceInput(kind=kind, filename=filename, content=content)
        return await self._process(source_id, filename, kind, len(content), source)

    async def ingest_url(self, url: str, kind: str = "auto") -> SourceOut:
        validate_url(url)
        if kind == "auto":
            kind = "wikipedia" if "wikipedia.org/wiki/" in url else "web"
        source_id = uuid.uuid4().hex
        source = SourceInput(kind=kind, url=url, filename=url)
        return await self._process(source_id, url, kind, 0, source)

    async def _process(self, source_id: str, name: str, kind: str, size: int, source: SourceInput) -> SourceOut:
        loader = self._loaders.get(kind)
        if not loader:
            raise IngestionError(f"No loader registered for kind '{kind}'")
        try:
            documents = await loader.load(source)
        except IngestionError:
            raise
        except Exception as exc:
            raise IngestionError(f"Ingestion failed: {exc}") from exc

        chunker: IChunker = self._chunker_factory(kind)
        all_chunks = []
        for doc in documents:
            md = {**doc.metadata, "source_id": source_id, "kind": kind, "name": name}
            all_chunks.extend(chunker.chunk(doc.text, md))
        if not all_chunks:
            raise IngestionError("No chunks produced from source")

        # Embed with per-chunk cache
        embeddings: list[list[float]] = []
        to_embed_indices: list[int] = []
        to_embed_texts: list[str] = []
        for i, c in enumerate(all_chunks):
            cached = await self._cache.get(embedding_key(c.text))
            if isinstance(cached, list) and len(cached) == self._embedder.dimension:
                embeddings.append(cached)
            else:
                embeddings.append([])
                to_embed_indices.append(i)
                to_embed_texts.append(c.text)

        if to_embed_texts:
            new_vecs = await self._embedder.embed(to_embed_texts)
            for idx, vec in zip(to_embed_indices, new_vecs):
                embeddings[idx] = vec
                await self._cache.set(
                    embedding_key(all_chunks[idx].text), vec, ttl=self._settings.cache_ttl_embeddings
                )

        records = [
            VectorRecord(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{source_id}:{i}")),
                source_id=source_id,
                text=c.text,
                metadata=c.metadata,
                embedding=embeddings[i],
            )
            for i, c in enumerate(all_chunks)
        ]
        await self._vs.upsert(records)

        # Invalidate dependent caches (source set changed)
        await self._cache.delete_pattern("resp:*")
        await self._cache.delete_pattern("ret:*")

        source_out = SourceOut(
            source_id=source_id,
            kind=kind,
            name=name,
            chunks=len(records),
            bytes=size,
            status="ready",
            created_at=datetime.now(timezone.utc),
        )
        self._sources[source_id] = source_out
        log.info("source_ingested", source_id=source_id, chunks=len(records), kind=kind)
        return source_out

    async def list_sources(self) -> list[SourceOut]:
        return sorted(self._sources.values(), key=lambda s: s.created_at, reverse=True)

    async def delete_source(self, source_id: str) -> None:
        if source_id not in self._sources:
            raise NotFoundError(f"Source {source_id} not found")
        await self._vs.delete_source(source_id)
        self._sources.pop(source_id, None)
        await self._cache.delete_pattern("resp:*")
        await self._cache.delete_pattern("ret:*")

    def current_source_ids(self) -> list[str]:
        return sorted(self._sources.keys())

    def current_source_set_hash(self) -> str:
        return source_set_hash(self.current_source_ids())

    @staticmethod
    def _infer_kind(filename: str) -> str:
        lower = filename.lower()
        if lower.endswith(".pdf"): return "pdf"
        if lower.endswith(".docx"): return "docx"
        if lower.endswith((".ppt", ".pptx")): return "pptx"
        if lower.endswith(".wav"): return "audio"
        if lower.endswith(".txt"): return "txt"
        from app.domains.ingestion.loaders.code_loader import is_code_file
        if is_code_file(filename): return "code"
        raise IngestionError(f"Cannot infer file kind from name: {filename}")