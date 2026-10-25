from app.domains.ingestion.embedders.base import IEmbedder
from app.domains.retrieval.schemas import RetrievalResult, RetrievedChunk
from app.infrastructure.cache.cache_keys import retrieval_key
from app.infrastructure.cache.redis_adapter import RedisCacheAdapter
from app.infrastructure.vectorstore.base import IVectorStore


class RetrievalService:
    def __init__(self, embedder: IEmbedder, vector_store: IVectorStore, cache: RedisCacheAdapter, top_k: int = 6):
        self._embedder = embedder
        self._vs = vector_store
        self._cache = cache
        self._top_k = top_k

    async def retrieve(self, query: str, source_ids: list[str] | None = None) -> RetrievalResult:
        query_vec = await self._embedder.embed_query(query)
        key = retrieval_key(query_vec, self._top_k, {"source_ids": source_ids or []})
        cached = await self._cache.get(key)
        if isinstance(cached, dict) and "chunks" in cached:
            chunks = [RetrievedChunk(**c) for c in cached["chunks"]]
            return RetrievalResult(chunks=chunks, cache_hit=True)
        results = await self._vs.search(query_vec, top_k=self._top_k, source_ids=source_ids)
        await self._cache.set(key, {"chunks": [c.__dict__ for c in results]}, ttl=3600)
        return RetrievalResult(chunks=results, cache_hit=False)