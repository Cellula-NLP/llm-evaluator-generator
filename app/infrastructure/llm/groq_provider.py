from langchain_groq import ChatGroq

from app.config.settings import Settings
from app.infrastructure.llm.base import ILLMProvider


class GroqProvider(ILLMProvider):
    def __init__(self, settings: Settings):
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for the Groq provider")
        self._generator = ChatGroq(
            model=settings.generator_model,
            temperature=settings.llm_temperature,
            api_key=settings.groq_api_key,
            timeout=settings.llm_timeout_seconds,
        )
        self._evaluator = ChatGroq(
            model=settings.evaluator_model,
            temperature=0.0,
            api_key=settings.groq_api_key,
            timeout=settings.llm_timeout_seconds,
        )

    @property
    def generator(self): return self._generator

    @property
    def evaluator(self): return self._evaluator