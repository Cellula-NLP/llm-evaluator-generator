from app.domains.ingestion.chunkers.base import Chunk, IChunker
from app.domains.ingestion.chunkers.recursive_chunker import RecursiveChunker


class SemanticChunker(IChunker):
    """Placeholder — falls back to recursive. Upgrade point for embedding-based splitting."""

    def __init__(self):
        self._fallback = RecursiveChunker()

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        return self._fallback.chunk(text, metadata)