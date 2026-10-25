import asyncio

from sentence_transformers import SentenceTransformer

from app.config.settings import get_settings
from app.domains.ingestion.embedders.base import IEmbedder


class SentenceTransformerEmbedder(IEmbedder):
    def __init__(self, model_name: str | None = None):
        s = get_settings()
        self._model = SentenceTransformer(model_name or s.embedding_model)
        self._dim = self._model.get_sentence_embedding_dimension()
        self._batch = s.embedding_batch_size

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        def _run() -> list[list[float]]:
            return self._model.encode(texts, batch_size=self._batch, show_progress_bar=False).tolist()

        return await asyncio.to_thread(_run)

    async def embed_query(self, text: str) -> list[float]:
        vecs = await self.embed([text])
        return vecs[0]