from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.domains.agents.router import router as agents_router
from app.domains.ingestion.router import router as ingestion_router
from app.shared.dependencies import init_resources, shutdown_resources
from app.shared.exceptions import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.shared.middleware import RequestContextMiddleware, SessionMiddleware
from app.ui.router import router as ui_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_resources()
    yield
    await shutdown_resources()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SessionMiddleware)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    static_dir = Path(__file__).parent / "ui" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(ingestion_router)
    app.include_router(agents_router)
    app.include_router(ui_router)

    @app.get("/")
    async def root():
        return {"app": settings.app_name, "ui": "/ui/ingest", "docs": "/docs"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()