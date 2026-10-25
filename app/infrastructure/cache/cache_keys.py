import hashlib
import json


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def embedding_key(text: str) -> str:
    return f"emb:{_hash(text)}"


def retrieval_key(query_embedding: list[float], top_k: int, filters: dict) -> str:
    payload = json.dumps({"v": [round(x, 5) for x in query_embedding[:16]], "top_k": top_k, "filters": filters}, sort_keys=True)
    return f"ret:{_hash(payload)}"


def source_set_hash(source_ids: list[str]) -> str:
    return _hash("|".join(sorted(source_ids)))