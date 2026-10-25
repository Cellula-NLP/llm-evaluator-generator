from urllib.parse import unquote, urlparse

import httpx

from app.domains.ingestion.loaders.base import IDocumentLoader, LoadedDocument, SourceInput
from app.shared.exceptions import IngestionError


class WikipediaLoader(IDocumentLoader):
    kind = "wikipedia"

    async def load(self, source: SourceInput) -> list[LoadedDocument]:
        if not source.url:
            raise IngestionError("Wikipedia source requires URL")
        title = self._extract_title(source.url)
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(api_url, headers={"User-Agent": "NLP-EvalGen/1.0"})
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                raise IngestionError(f"Wikipedia fetch failed: {exc}") from exc
        text = data.get("extract") or ""
        if not text:
            raise IngestionError("Wikipedia page has no extractable content")
        return [LoadedDocument(text=text, metadata={"url": source.url, "title": data.get("title", title)})]

    @staticmethod
    def _extract_title(url: str) -> str:
        path = urlparse(url).path
        if "/wiki/" in path:
            return unquote(path.split("/wiki/", 1)[1])
        raise IngestionError("URL is not a Wikipedia article")