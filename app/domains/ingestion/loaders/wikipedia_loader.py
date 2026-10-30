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

        # Use MediaWiki API to fetch the FULL text
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,  # Plain text instead of HTML
            "titles": title,
            "format": "json",
            "redirects": 1,  # Follow redirects automatically
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.get(api_url, params=params, headers={"User-Agent": "NLP-EvalGen/1.0"})
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                raise IngestionError(f"Wikipedia fetch failed: {exc}") from exc

        # Parse the MediaWiki JSON structure
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            raise IngestionError("Wikipedia page not found")

        page = next(iter(pages.values()))
        text = page.get("extract", "")

        if not text.strip():
            raise IngestionError("Wikipedia page has no extractable content")

        return [LoadedDocument(text=text, metadata={"url": source.url, "title": page.get("title", title)})]

    @staticmethod
    def _extract_title(url: str) -> str:
        path = urlparse(url).path
        if "/wiki/" in path:
            return unquote(path.split("/wiki/", 1)[1])
        raise IngestionError("URL is not a Wikipedia article")