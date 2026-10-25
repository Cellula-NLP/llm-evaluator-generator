from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.domains.ingestion.schemas import IngestResponse, SourceOut, UrlIngestRequest
from app.domains.ingestion.service import IngestionService
from app.shared.dependencies import get_ingestion_service

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    kind: str | None = Form(None),
    service: IngestionService = Depends(get_ingestion_service),
):
    content = await file.read()
    source = await service.ingest_file(file.filename or "upload", content, kind=kind)
    return IngestResponse(source=source)


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(payload: UrlIngestRequest, service: IngestionService = Depends(get_ingestion_service)):
    source = await service.ingest_url(payload.url, kind=payload.kind)
    return IngestResponse(source=source)


@router.get("/sources", response_model=list[SourceOut])
async def list_sources(service: IngestionService = Depends(get_ingestion_service)):
    return await service.list_sources()


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(source_id: str, service: IngestionService = Depends(get_ingestion_service)):
    await service.delete_source(source_id)