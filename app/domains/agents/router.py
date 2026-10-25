from fastapi import APIRouter, Depends

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
    return await controller.run(session_id, payload.question, source_ids=payload.source_ids)