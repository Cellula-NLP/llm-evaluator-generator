from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

SourceKind = Literal["pdf", "docx", "pptx", "txt", "code", "web", "wikipedia", "audio"]


@dataclass
class LoadedDocument:
    text: str
    metadata: dict


@dataclass
class SourceInput:
    kind: SourceKind
    filename: str | None = None
    content: bytes | None = None
    url: str | None = None


class IDocumentLoader(ABC):
    kind: SourceKind

    @abstractmethod
    async def load(self, source: SourceInput) -> list[LoadedDocument]: ...