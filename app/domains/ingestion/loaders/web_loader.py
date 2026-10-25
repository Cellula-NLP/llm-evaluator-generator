import httpx
from bs4 import BeautifulSoup

from app.config.settings import get_settings
from app.domains.ingestion.loaders.base import IDocumentLoader, LoadedDocument, SourceInput
from app.shared.exceptions import IngestionError


class WebLoader(IDocumentLoader):
    kind = "web"

    async def load(self, source: SourceInput) -> list[LoadedDocument]:
        if not source.url:
            raise IngestionError("Web source requires URL")
        s = get_settings()
        async with httpx.AsyncClient(
            timeout=s.url_timeout_seconds, follow_redirects=True, max_redirects=s.max_url_redirects
        ) as client:
            try:
                resp = await client.get(source.url, headers={"User-Agent": "NLP-EvalGen/1.0"})
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise IngestionError(f"Failed to fetch URL: {exc}") from exc
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if not text:
            raise IngestionError("Web page contains no extractable text")
        title = soup.title.string if soup.title else ""
        return [LoadedDocument(text=text, metadata={"url": source.url, "title": title})]