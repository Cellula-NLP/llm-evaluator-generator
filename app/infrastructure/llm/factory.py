from app.config.settings import Settings
from app.infrastructure.llm.base import ILLMProvider
from app.infrastructure.llm.groq_provider import GroqProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider
from app.infrastructure.llm.openai_provider import OpenAIProvider


def build_llm_provider(settings: Settings) -> ILLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIProvider(settings)
    if settings.llm_provider == "groq":
        return GroqProvider(settings)
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")