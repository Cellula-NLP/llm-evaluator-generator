import json
from typing import Any

import redis.asyncio as redis

from app.shared.exceptions import CacheError


class RedisCacheAdapter:
    def __init__(self, client: redis.Redis):
        self._client = client

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._client.get(key)
        except Exception as exc:
            raise CacheError(f"Redis GET failed: {exc}") from exc
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw.decode("utf-8", errors="replace")

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        payload = value if isinstance(value, (str, bytes)) else json.dumps(value)
        try:
            await self._client.set(key, payload, ex=ttl)
        except Exception as exc:
            raise CacheError(f"Redis SET failed: {exc}") from exc

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except Exception as exc:
            raise CacheError(f"Redis DEL failed: {exc}") from exc

    async def delete_pattern(self, pattern: str) -> int:
        deleted = 0
        try:
            async for key in self._client.scan_iter(match=pattern):
                await self._client.delete(key)
                deleted += 1
        except Exception as exc:
            raise CacheError(f"Redis SCAN/DEL failed: {exc}") from exc
        return deleted

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()