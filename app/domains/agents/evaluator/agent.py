import structlog

from app.domains.agents.evaluator.memory import EvaluatorMemory
from app.domains.agents.schemas import EvaluationResult

log = structlog.get_logger()


class EvaluatorAgent:
    def __init__(self, chain, memory: EvaluatorMemory):
        self._chain = chain
        self._memory = memory

    async def evaluate(self, session_id: str, question: str, context: str, answer: str) -> EvaluationResult:
        try:
            result: EvaluationResult = await self._chain.ainvoke(
                {"question": question, "context": context, "answer": answer}
            )
        except Exception as exc:
            log.warning("evaluator_parse_failed", session_id=session_id, error=str(exc))
            # Fallback to prevent app crash, forcing generator to retry
            result = EvaluationResult(
                is_acceptable=False,
                accuracy=1,
                relevance=1,
                completeness=1,
                consistency_with_sources=1,
                grounded=False,
                unsupported_claims=[],
                feedback="Evaluator failed to parse response. Please ensure the answer is well-structured and try again."
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