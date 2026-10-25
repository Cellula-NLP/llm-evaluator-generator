from datetime import datetime

from pydantic import BaseModel, Field


class SourceOut(BaseModel):
    source_id: str
    kind: str
    name: str
    chunks: int
    bytes: int
    status: str
    created_at: datetime


class IngestResponse(BaseModel):
    source: SourceOut


class UrlIngestRequest(BaseModel):
    url: str = Field(..., min_length=1)
    kind: str = "auto"