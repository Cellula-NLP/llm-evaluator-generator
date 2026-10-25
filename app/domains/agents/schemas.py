from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    is_acceptable: bool = Field(description="True if the answer is satisfactory")
    accuracy: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    consistency_with_sources: int = Field(ge=1, le=5)
    grounded: bool
    unsupported_claims: list[str] = []
    feedback: str = Field(description="If not acceptable, concrete guidance to improve")


class IterationTrace(BaseModel):
    iteration: int
    answer: str
    evaluation: EvaluationResult | None = None
    feedback: str | None = None


class FinalAnswer(BaseModel):
    answer: str
    validated: bool
    iterations: int
    cache_hit: bool = False
    grounded: bool = False
    refusal: bool = False
    warning: str | None = None
    trace: list[IterationTrace] = []


class QueryRequest(BaseModel):
    question: str
    source_ids: list[str] | None = None