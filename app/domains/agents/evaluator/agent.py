import structlog

from app.domains.agents.evaluator.memory import EvaluatorMemory
from app.domains.agents.schemas import EvaluationResult

log = structlog.get_logger()


class EvaluatorAgent:
    def __init__(self, chain, memory: EvaluatorMemory):
        self._chain = chain
        self._memory = memory

    async def evaluate(self, session_id: str, question: str, context: str, answer: str) -> EvaluationResult:
        result: EvaluationResult = await self._chain.ainvoke(
            {"question": question, "context": context, "answer": answer}
        )
        await self._memory.record(
            session_id,
            {"acceptable": result.is_acceptable, "grounded": result.grounded, "scores": {
                "accuracy": result.accuracy,
                "relevance": result.relevance,
                "completeness": result.completeness,
                "consistency": result.consistency_with_sources,
            }},
        )
        log.info("evaluated", session_id=session_id, acceptable=result.is_acceptable, grounded=result.grounded)
        return result