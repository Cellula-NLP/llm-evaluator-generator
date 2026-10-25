from langchain_openai import ChatOpenAI

from app.config.settings import Settings
from app.infrastructure.llm.base import ILLMProvider


class OpenAIProvider(ILLMProvider):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI provider")
        self._generator = ChatOpenAI(
            model=settings.generator_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_seconds,
        )
        self._evaluator = ChatOpenAI(
            model=settings.evaluator_model,
            temperature=0.0,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.llm_timeout_seconds,
        )

    @property
    def generator(self): return self._generator

    @property
    def evaluator(self): return self._evaluator