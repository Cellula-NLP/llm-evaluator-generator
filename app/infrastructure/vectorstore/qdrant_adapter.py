from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.infrastructure.vectorstore.base import IVectorStore, RetrievedChunk, VectorRecord


class QdrantAdapter(IVectorStore):
    def __init__(self, client: AsyncQdrantClient, collection: str):
        self._client = client
        self._collection = collection

    async def ensure_collection(self, dim: int) -> None:
        existing = await self._client.get_collections()
        if self._collection not in {c.name for c in existing.collections}:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    async def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        points = [
            PointStruct(
                id=r.id,
                vector=r.embedding,
                payload={"source_id": r.source_id, "text": r.text, **r.metadata},
            )
            for r in records
        ]
        await self._client.upsert(collection_name=self._collection, points=points)

    async def search(
        self, embedding: list[float], top_k: int, source_ids: list[str] | None = None
    ) -> list[RetrievedChunk]:
        query_filter = None
        if source_ids:
            query_filter = Filter(
                should=[FieldCondition(key="source_id", match=MatchValue(value=sid)) for sid in source_ids]
            )
        hits = await self._client.search(
            collection_name=self._collection,
            query_vector=embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            RetrievedChunk(
                id=str(hit.id),
                source_id=hit.payload.get("source_id", ""),
                text=hit.payload.get("text", ""),
                metadata={k: v for k, v in hit.payload.items() if k not in ("text", "source_id")},
                score=float(hit.score),
            )
            for hit in hits
        ]

    async def delete_source(self, source_id: str) -> None:
        await self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]),
        )

    async def count(self) -> int:
        try:
            result = await self._client.count(collection_name=self._collection)
            return int(result.count)
        except Exception:
            return 0