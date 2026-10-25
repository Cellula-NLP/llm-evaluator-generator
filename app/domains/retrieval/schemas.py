from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    id: str
    source_id: str
    text: str
    score: float


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    cache_hit: bool = False

    def as_context(self) -> str:
        return "\n\n---\n\n".join(c.text for c in self.chunks)