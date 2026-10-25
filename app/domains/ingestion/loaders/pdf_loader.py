import fitz  # PyMuPDF

from app.domains.ingestion.loaders.base import IDocumentLoader, LoadedDocument, SourceInput
from app.shared.exceptions import IngestionError


class PDFLoader(IDocumentLoader):
    kind = "pdf"

    async def load(self, source: SourceInput) -> list[LoadedDocument]:
        if not source.content:
            raise IngestionError("PDF content is empty")
        try:
            doc = fitz.open(stream=source.content, filetype="pdf")
        except Exception as exc:
            raise IngestionError(f"Failed to open PDF: {exc}") from exc

        pages: list[LoadedDocument] = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append(LoadedDocument(text=text, metadata={"page": i + 1, "filename": source.filename}))
        doc.close()
        if not pages:
            raise IngestionError("PDF contains no extractable text")
        return pages