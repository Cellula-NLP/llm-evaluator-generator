from abc import ABC, abstractmethod


class ISpeechToText(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str: ...