from app.domains.agents.evaluator.prompts import build_evaluator_prompt
from app.domains.agents.schemas import EvaluationResult
from app.infrastructure.llm.base import ILLMProvider


def build_evaluator_chain(llm_provider: ILLMProvider):
    return build_evaluator_prompt() | llm_provider.evaluator.with_structured_output(EvaluationResult)