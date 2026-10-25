import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

log = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        log.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        structlog.contextvars.unbind_contextvars("request_id", "path")
        response.headers["x-request-id"] = request_id
        return response


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        sid = request.cookies.get("session_id")
        new_session = sid is None
        if new_session:
            sid = uuid.uuid4().hex
        request.state.session_id = sid
        response = await call_next(request)
        if new_session:
            response.set_cookie("session_id", sid, httponly=True, samesite="lax", max_age=86400)
        return response