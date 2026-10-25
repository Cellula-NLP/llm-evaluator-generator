import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = structlog.get_logger()


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class IngestionError(AppError):
    status_code = 400
    code = "ingestion_error"


class UnsupportedFormatError(IngestionError):
    code = "unsupported_format"


class LLMError(AppError):
    status_code = 502
    code = "llm_error"


class CacheError(AppError):
    status_code = 502
    code = "cache_error"


async def app_error_handler(request: Request, exc: AppError):
    log.warning("app_error", code=exc.code, message=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": str(exc)}},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "validation_error", "message": "Invalid request", "details": exc.errors()}},
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    log.exception("unhandled_error", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Internal server error"}},
    )