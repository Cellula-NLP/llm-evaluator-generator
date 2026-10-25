from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VectorRecord:
    id: str
    source_id: str
    text: str
    metadata: dict
    embedding: list[float] | None = None


@dataclass
class RetrievedChunk:
    id: str
    source_id: str
    text: str
    metadata: dict
    score: float


class IVectorStore(ABC):
    @abstractmethod
    async def ensure_collection(self, dim: int) -> None: ...

    @abstractmethod
    async def upsert(self, records: list[VectorRecord]) -> None: ...

    @abstractmethod
    async def search(
        self, embedding: list[float], top_k: int, source_ids: list[str] | None = None
    ) -> list[RetrievedChunk]: ...

    @abstractmethod
    async def delete_source(self, source_id: str) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...