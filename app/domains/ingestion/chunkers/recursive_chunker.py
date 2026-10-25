from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import get_settings
from app.domains.ingestion.chunkers.base import Chunk, IChunker


class RecursiveChunker(IChunker):
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        s = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or s.chunk_size,
            chunk_overlap=chunk_overlap or s.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        parts = self._splitter.split_text(text)
        return [
            Chunk(text=p, metadata={**metadata, "chunk_index": i})
            for i, p in enumerate(parts)
            if p.strip()
        ]