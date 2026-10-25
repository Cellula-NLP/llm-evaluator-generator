from langchain_core.prompts import ChatPromptTemplate

EVALUATOR_SYSTEM = """You are a strict QA evaluator.

Judge the candidate answer against the question and External Knowledge. Score each dimension 1-5:
- accuracy: factually correct given the context
- relevance: addresses the question
- completeness: covers what the context allows
- consistency_with_sources: does not contradict the context

Set grounded=true only if every claim is supported by the context.
If grounded=false, list unsupported_claims.
If the answer is the exact refusal string, treat it as acceptable ONLY IF the context truly lacks the answer.

Return structured output only.
"""

EVALUATOR_HUMAN = """Question:
{question}

External Knowledge:
{context}

Candidate Answer:
{answer}

Evaluate and return the structured result."""


def build_evaluator_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("system", EVALUATOR_SYSTEM), ("human", EVALUATOR_HUMAN)])