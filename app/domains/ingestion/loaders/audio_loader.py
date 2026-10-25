from app.domains.ingestion.loaders.base import IDocumentLoader, LoadedDocument, SourceInput
from app.infrastructure.speech.base import ISpeechToText
from app.shared.exceptions import IngestionError


class AudioLoader(IDocumentLoader):
    kind = "audio"

    def __init__(self, speech: ISpeechToText):
        self._speech = speech

    async def load(self, source: SourceInput) -> list[LoadedDocument]:
        if not source.content:
            raise IngestionError("Audio content is empty")
        try:
            transcript = await self._speech.transcribe(source.content)
        except Exception as exc:
            raise IngestionError(f"Transcription failed: {exc}") from exc
        if not transcript.strip():
            raise IngestionError("Audio produced empty transcript")
        return [LoadedDocument(text=transcript, metadata={"filename": source.filename, "media_type": "audio/wav"})]