from dataclasses import dataclass, field

from app.domains.agents.schemas import EvaluationResult, IterationTrace


@dataclass
class LoopState:
    question: str
    context: str
    current_answer: str = ""
    last_evaluation: EvaluationResult | None = None
    final_validated: bool = False
    warning: str | None = None
    iterations: list[IterationTrace] = field(default_factory=list)