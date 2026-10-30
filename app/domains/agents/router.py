from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.domains.agents.loop.controller import LoopController
from app.domains.agents.schemas import FinalAnswer, QueryRequest
from app.shared.dependencies import get_loop_controller, get_session_id

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=FinalAnswer)
async def query(
    payload: QueryRequest,
    session_id: str = Depends(get_session_id),
    controller: LoopController = Depends(get_loop_controller),
) -> FinalAnswer:
    """Standard synchronous endpoint (kept for Swagger/API clients)."""
    return await controller.run(session_id, payload.question, source_ids=payload.source_ids)


@router.post("/query/stream")
async def query_stream(
    payload: QueryRequest,
    session_id: str = Depends(get_session_id),
    controller: LoopController = Depends(get_loop_controller),
):
    """Streaming endpoint for the UI."""
    return StreamingResponse(
        controller.run_stream(session_id, payload.question, source_ids=payload.source_ids),
        media_type="text/event-stream",
    )