import structlog

from app.domains.agents.generator.memory import GeneratorMemory
from app.domains.agents.generator.prompts import REFUSAL_MARKER

log = structlog.get_logger()


class GeneratorAgent:
    def __init__(self, chain, memory: GeneratorMemory):
        self._chain = chain
        self._memory = memory

    async def generate(
            self,
            session_id: str,
            question: str,
            context: str,
            previous_answer: str = "",
            feedback: str = "",
    ) -> str:
        # Fetch recent conversation history
        recent_mem = await self._memory.recent(session_id, n=3)
        history_str = "\n".join(
            [f"User: {m['question']}\nAssistant: {m['answer']}" for m in recent_mem if
             'question' in m and 'answer' in m]
        )
        if not history_str:
            history_str = "(No previous conversation)"

        answer = await self._chain.ainvoke(
            {
                "question": question,
                "context": context,
                "history": history_str,
                "previous_answer": previous_answer or "(none)",
                "feedback": feedback or "(none)",
            }
        )
        answer = answer.strip()

        # Save the new interaction to memory
        await self._memory.record(
            session_id,
            {"question": question, "answer": answer, "had_feedback": bool(feedback),
             "refused": answer == REFUSAL_MARKER},
        )
        log.info("generator_answered", session_id=session_id, length=len(answer), refused=answer == REFUSAL_MARKER)
        return answer