from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.domains.ingestion.service import IngestionService
from app.infrastructure.cache.redis_adapter import RedisCacheAdapter
from app.infrastructure.vectorstore.qdrant_adapter import QdrantAdapter
from app.shared.dependencies import get_cache, get_ingestion_service, get_vector_store

router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/ingest", response_class=HTMLResponse)
async def ingest_page(request: Request):
    # Updated for new Starlette signature: request first, then name
    return templates.TemplateResponse(request=request, name="ingest.html")


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(
    request: Request,
    service: IngestionService = Depends(get_ingestion_service),
):
    sources = await service.list_sources()
    return templates.TemplateResponse(request=request, name="sources.html", context={"sources": sources})


@router.get("/ask", response_class=HTMLResponse)
async def ask_page(request: Request):
    return templates.TemplateResponse(request=request, name="ask.html")


@router.get("/health", response_class=HTMLResponse)
async def health_page(
    request: Request,
    cache: RedisCacheAdapter = Depends(get_cache),
    vs: QdrantAdapter = Depends(get_vector_store),
):
    redis_ok = await cache.ping()
    count = await vs.count()
    return templates.TemplateResponse(
        request=request,
        name="health.html",
        context={"redis_ok": redis_ok, "vector_count": count}
    )