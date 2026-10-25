import os

from app.domains.ingestion.loaders.base import IDocumentLoader, LoadedDocument, SourceInput
from app.shared.exceptions import IngestionError

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".cs", ".kt", ".swift", ".scala", ".sh", ".sql", ".html", ".css",
    ".json", ".yaml", ".yml", ".toml", ".md",
}


def is_code_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in CODE_EXTENSIONS


class CodeLoader(IDocumentLoader):
    kind = "code"

    async def load(self, source: SourceInput) -> list[LoadedDocument]:
        if not source.content:
            raise IngestionError("Code content is empty")
        try:
            text = source.content.decode("utf-8")
        except UnicodeDecodeError:
            text = source.content.decode("latin-1", errors="replace")
        if not text.strip():
            raise IngestionError("Code file contains no text")
        filename = source.filename or "untitled"
        language = os.path.splitext(filename)[1].lstrip(".") or "text"
        return [LoadedDocument(text=text, metadata={"filename": filename, "language": language})]