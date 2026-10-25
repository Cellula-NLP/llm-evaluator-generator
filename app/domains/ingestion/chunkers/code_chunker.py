import re

from app.config.settings import get_settings
from app.domains.ingestion.chunkers.base import Chunk, IChunker

BOUNDARY = re.compile(
    r"^(?=(?:def |class |function |async function |func |public |private |protected |void |int |export ))",
    re.M,
)


class CodeChunker(IChunker):
    def __init__(self):
        self._s = get_settings()

    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        segments = [s.strip() for s in BOUNDARY.split(text) if s and s.strip()]
        chunks: list[Chunk] = []
        buf = ""
        for seg in segments:
            if len(buf) + len(seg) + 2 <= self._s.chunk_size:
                buf = (buf + "\n\n" + seg).strip()
            else:
                if buf:
                    chunks.append(Chunk(text=buf, metadata={**metadata, "chunk_index": len(chunks)}))
                buf = seg
        if buf:
            chunks.append(Chunk(text=buf, metadata={**metadata, "chunk_index": len(chunks)}))
        return chunks