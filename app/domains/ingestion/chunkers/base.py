from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    metadata: dict


class IChunker(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: dict) -> list[Chunk]: ...