import json
import structlog
from typing import AsyncGenerator

from app.domains.agents.evaluator.agent import EvaluatorAgent
from app.domains.agents.generator.agent import GeneratorAgent
from app.domains.agents.generator.prompts import REFUSAL_MARKER
from app.domains.agents.loop.state import LoopState
from app.domains.agents.schemas import FinalAnswer, IterationTrace

log = structlog.get_logger()


class LoopController:
    def __init__(
            self,
            generator: GeneratorAgent,
            evaluator: EvaluatorAgent,
            retrieval_service,
            max_iterations: int = 4,
    ):
        self._generator = generator
        self._evaluator = evaluator
        self._retrieval = retrieval_service
        self._max = max_iterations

    async def run_stream(
            self, session_id: str, question: str, source_ids: list[str] | None = None
    ) -> AsyncGenerator[str, None]:

        def format_sse(event: str, data: dict) -> str:
            return f"data: {json.dumps({'event': event, 'data': data})}\n\n"

        yield format_sse("status", {"message": "Retrieving context..."})

        retrieval = await self._retrieval.retrieve(question, source_ids=source_ids)
        context = retrieval.as_context()
        state = LoopState(question=question, context=context)

        if not context.strip():
            final_answer = FinalAnswer(
                answer=REFUSAL_MARKER, validated=True, iterations=0,
                cache_hit=retrieval.cache_hit, grounded=False, refusal=True,
            )
            yield format_sse("final", final_answer.model_dump())
            return

        yield format_sse("status", {"message": "Generating initial answer..."})
        state.current_answer = await self._generator.generate(
            session_id=session_id, question=question, context=context
        )

        for iteration in range(1, self._max + 1):
            yield format_sse("status", {"message": f"Evaluating iteration {iteration}..."})

            evaluation = await self._evaluator.evaluate(
                session_id=session_id, question=question, context=context, answer=state.current_answer
            )
            state.last_evaluation = evaluation
            trace = IterationTrace(
                iteration=iteration,
                answer=state.current_answer,
                evaluation=evaluation,
                feedback=evaluation.feedback if not evaluation.is_acceptable else None,
            )
            state.iterations.append(trace)

            # Stream the iteration result immediately
            yield format_sse("iteration", trace.model_dump())

            if evaluation.is_acceptable:
                state.final_validated = True
                break

            if iteration == self._max:
                state.warning = f"Maximum iterations ({self._max}) reached without an acceptable answer"
                break

            yield format_sse("status", {"message": f"Applying feedback (Iteration {iteration + 1})..."})

            # Re-retrieve based on feedback
            augmented_query = f"{question} {evaluation.feedback}"
            new_retrieval = await self._retrieval.retrieve(augmented_query, source_ids=source_ids)
            state.context = new_retrieval.as_context() or context

            state.current_answer = await self._generator.generate(
                session_id=session_id,
                question=question,
                context=state.context,
                previous_answer=state.current_answer,
                feedback=evaluation.feedback,
            )

        refusal = state.current_answer == REFUSAL_MARKER
        grounded = state.last_evaluation.grounded if state.last_evaluation else False

        final_answer = FinalAnswer(
            answer=state.current_answer,
            validated=state.final_validated,
            iterations=len(state.iterations),
            cache_hit=retrieval.cache_hit,
            grounded=grounded,
            refusal=refusal,
            warning=state.warning,
            trace=state.iterations,
        )

        yield format_sse("final", final_answer.model_dump())