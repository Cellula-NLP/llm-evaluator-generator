import structlog

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

    async def run(self, session_id: str, question: str, source_ids: list[str] | None = None) -> FinalAnswer:
        # Initial Retrieval
        retrieval = await self._retrieval.retrieve(question, source_ids=source_ids)
        context = retrieval.as_context()
        state = LoopState(question=question, context=context)

        if not context.strip():
            return FinalAnswer(
                answer=REFUSAL_MARKER,
                validated=True,
                iterations=0,
                cache_hit=retrieval.cache_hit,
                grounded=False,
                refusal=True,
            )

        state.current_answer = await self._generator.generate(
            session_id=session_id, question=question, context=context
        )

        for iteration in range(1, self._max + 1):
            evaluation = await self._evaluator.evaluate(
                session_id=session_id, question=question, context=context, answer=state.current_answer
            )
            state.last_evaluation = evaluation
            state.iterations.append(
                IterationTrace(
                    iteration=iteration,
                    answer=state.current_answer,
                    evaluation=evaluation,
                    feedback=evaluation.feedback if not evaluation.is_acceptable else None,
                )
            )

            if evaluation.is_acceptable:
                state.final_validated = True
                break

            if iteration == self._max:
                state.warning = f"Maximum iterations ({self._max}) reached without an acceptable answer"
                break

            # Dynamic Re-Retrieval based on Feedback
            # If the answer wasn't acceptable, use the Evaluator's feedback to find the missing information.
            augmented_query = f"{question} {evaluation.feedback}"
            new_retrieval = await self._retrieval.retrieve(augmented_query, source_ids=source_ids)

            # Update the context for the next iteration
            state.context = new_retrieval.as_context()
            # If the new retrieval found nothing, fallback to original context
            if not state.context.strip():
                state.context = context
            # -----------------------------------------------------------

            state.current_answer = await self._generator.generate(
                session_id=session_id,
                question=question,
                context=state.context,  # Using the newly retrieved context
                previous_answer=state.current_answer,
                feedback=evaluation.feedback,
            )

        refusal = state.current_answer == REFUSAL_MARKER
        grounded = state.last_evaluation.grounded if state.last_evaluation else False
        log.info(
            "loop_complete",
            session_id=session_id,
            validated=state.final_validated,
            iterations=len(state.iterations),
            refusal=refusal,
        )
        return FinalAnswer(
            answer=state.current_answer,
            validated=state.final_validated,
            iterations=len(state.iterations),
            cache_hit=retrieval.cache_hit,
            grounded=grounded,
            refusal=refusal,
            warning=state.warning,
            trace=state.iterations,
        )