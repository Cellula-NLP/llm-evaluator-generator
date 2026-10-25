import asyncio
import tempfile
from pathlib import Path

from app.infrastructure.speech.base import ISpeechToText


class WhisperAdapter(ISpeechToText):
    def __init__(self, model_name: str = "base"):
        self._model_name = model_name
        self._model = None

    def _ensure_model(self):
        # Lazy-load faster_whisper to prevent OpenMP conflicts with PyTorch at startup
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self._model_name, device="cpu", compute_type="int8")
        return self._model

    async def transcribe(self, audio_bytes: bytes) -> str:
        def _run() -> str:
            model = self._ensure_model()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                path = Path(tmp.name)
            try:
                segments, _ = model.transcribe(str(path), beam_size=1)
                return " ".join(seg.text.strip() for seg in segments).strip()
            finally:
                path.unlink(missing_ok=True)

        return await asyncio.to_thread(_run)