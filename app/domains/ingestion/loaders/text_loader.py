from app.domains.ingestion.loaders.base import IDocumentLoader, LoadedDocument, SourceInput
from app.shared.exceptions import IngestionError


class TextLoader(IDocumentLoader):
    kind = "txt"

    async def load(self, source: SourceInput) -> list[LoadedDocument]:
        if not source.content:
            raise IngestionError("TXT content is empty")
        try:
            text = source.content.decode("utf-8")
        except UnicodeDecodeError:
            text = source.content.decode("latin-1", errors="replace")
        if not text.strip():
            raise IngestionError("TXT contains no text")
        return [LoadedDocument(text=text, metadata={"filename": source.filename})]