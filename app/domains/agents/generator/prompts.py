from langchain_core.prompts import ChatPromptTemplate

GENERATOR_SYSTEM = """You are a careful, factual question-answering assistant.

Rules:
1. Answer ONLY using the provided External Knowledge context.
2. Do NOT use prior knowledge to invent facts.
3. If the context does not contain enough information, respond EXACTLY with:
   "The provided sources do not contain enough information to answer this question."
4. Keep answers concise and directly address the question.
5. When prior feedback is provided, apply it to improve the answer.
"""

GENERATOR_HUMAN = """External Knowledge:
{context}

Question:
{question}

Previous Answer (may be empty):
{previous_answer}

Feedback to apply (may be empty):
{feedback}

Produce the best grounded answer now."""

REFUSAL_MARKER = "The provided sources do not contain enough information to answer this question."


def build_generator_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("system", GENERATOR_SYSTEM), ("human", GENERATOR_HUMAN)])