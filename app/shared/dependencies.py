import uuid

import redis.asyncio as redis
from fastapi import Request
from qdrant_client import AsyncQdrantClient

from app.config.settings import get_settings
from app.domains.agents.evaluator.agent import EvaluatorAgent
from app.domains.agents.evaluator.chain import build_evaluator_chain
from app.domains.agents.evaluator.memory import EvaluatorMemory
from app.domains.agents.generator.agent import GeneratorAgent
from app.domains.agents.generator.chain import build_generator_chain
from app.domains.agents.generator.memory import GeneratorMemory
from app.domains.agents.loop.controller import LoopController
from app.domains.ingestion.chunkers.code_chunker import CodeChunker
from app.domains.ingestion.chunkers.recursive_chunker import RecursiveChunker
from app.domains.ingestion.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from app.domains.ingestion.loaders.audio_loader import AudioLoader
from app.domains.ingestion.loaders.code_loader import CodeLoader
from app.domains.ingestion.loaders.docx_loader import DOCXLoader
from app.domains.ingestion.loaders.pdf_loader import PDFLoader
from app.domains.ingestion.loaders.pptx_loader import PPTXLoader
from app.domains.ingestion.loaders.text_loader import TextLoader
from app.domains.ingestion.loaders.web_loader import WebLoader
from app.domains.ingestion.loaders.wikipedia_loader import WikipediaLoader
from app.domains.ingestion.service import IngestionService
from app.domains.retrieval.service import RetrievalService
from app.infrastructure.cache.redis_adapter import RedisCacheAdapter
from app.infrastructure.llm.factory import build_llm_provider
from app.infrastructure.speech.whisper_adapter import WhisperAdapter
from app.infrastructure.vectorstore.qdrant_adapter import QdrantAdapter

_redis_client: redis.Redis | None = None
_qdrant_client: AsyncQdrantClient | None = None
_cache_adapter: RedisCacheAdapter | None = None
_vector_store: QdrantAdapter | None = None
_ingestion_service: IngestionService | None = None
_retrieval_service: RetrievalService | None = None
_loop_controller: LoopController | None = None


async def init_resources() -> None:
    global _redis_client, _qdrant_client, _cache_adapter, _vector_store
    global _ingestion_service, _retrieval_service, _loop_controller

    s = get_settings()
    _redis_client = redis.from_url(s.redis_url, decode_responses=False)
    _cache_adapter = RedisCacheAdapter(_redis_client)

    _qdrant_client = AsyncQdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key)
    _vector_store = QdrantAdapter(_qdrant_client, s.qdrant_collection)

    embedder = SentenceTransformerEmbedder()
    await _vector_store.ensure_collection(embedder.dimension)

    llm_provider = build_llm_provider(s)
    speech = WhisperAdapter(s.whisper_model)

    loaders = {
        "pdf": PDFLoader(),
        "docx": DOCXLoader(),
        "pptx": PPTXLoader(),
        "txt": TextLoader(),
        "code": CodeLoader(),
        "web": WebLoader(),
        "wikipedia": WikipediaLoader(),
        "audio": AudioLoader(speech),
    }

    def chunker_factory(kind: str):
        return CodeChunker() if kind == "code" else RecursiveChunker()

    _ingestion_service = IngestionService(
        loaders=loaders,
        chunker_factory=chunker_factory,
        embedder=embedder,
        vector_store=_vector_store,
        cache=_cache_adapter,
        settings=s,
    )
    _retrieval_service = RetrievalService(
        embedder=embedder, vector_store=_vector_store, cache=_cache_adapter, top_k=s.retrieval_top_k
    )

    generator_memory = GeneratorMemory()
    evaluator_memory = EvaluatorMemory()
    generator = GeneratorAgent(build_generator_chain(llm_provider), generator_memory)
    evaluator = EvaluatorAgent(build_evaluator_chain(llm_provider), evaluator_memory)

    _loop_controller = LoopController(
        generator=generator,
        evaluator=evaluator,
        retrieval_service=_retrieval_service,
        max_iterations=s.max_iterations,
    )


async def shutdown_resources() -> None:
    if _cache_adapter is not None:
        await _cache_adapter.close()
    if _qdrant_client is not None:
        await _qdrant_client.close()


def get_cache() -> RedisCacheAdapter:
    assert _cache_adapter is not None
    return _cache_adapter


def get_vector_store() -> QdrantAdapter:
    assert _vector_store is not None
    return _vector_store


def get_ingestion_service() -> IngestionService:
    assert _ingestion_service is not None
    return _ingestion_service


def get_retrieval_service() -> RetrievalService:
    assert _retrieval_service is not None
    return _retrieval_service


def get_loop_controller() -> LoopController:
    assert _loop_controller is not None
    return _loop_controller


def get_session_id(request: Request) -> str:
    sid = getattr(request.state, "session_id", None)
    if not sid:
        sid = uuid.uuid4().hex
        request.state.session_id = sid
    return sid