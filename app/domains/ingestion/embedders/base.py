from abc import ABC, abstractmethod


class IEmbedder(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]: ...