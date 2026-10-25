from langchain_ollama import ChatOllama
from app.config.settings import Settings
from app.infrastructure.llm.base import ILLMProvider


class OllamaProvider(ILLMProvider):
    def __init__(self, settings: Settings):
        self._generator = ChatOllama(model=settings.generator_model, temperature=settings.llm_temperature)
        self._evaluator = ChatOllama(model=settings.evaluator_model, temperature=0.0)

    @property
    def generator(self): return self._generator

    @property
    def evaluator(self): return self._evaluator