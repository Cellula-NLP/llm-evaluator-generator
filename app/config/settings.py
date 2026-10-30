from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "LLM Evaluator-Generator"
    debug: bool = False
    log_level: str = "INFO"

    llm_provider: str = "openai"
    groq_api_key: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    generator_model: str = "gpt-4o-mini"
    evaluator_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 60

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_embeddings: int = 604800
    cache_ttl_retrieval: int = 3600

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "knowledge"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32

    max_file_size_mb: int = 50
    max_audio_size_mb: int = 200
    max_url_redirects: int = 5
    url_timeout_seconds: int = 20
    chunk_size: int = 1500
    chunk_overlap: int = 200

    retrieval_top_k: int = 10
    max_iterations: int = 4
    whisper_model: str = "base"


@lru_cache
def get_settings() -> Settings:
    return Settings()