import functools
from typing import Any, Callable

from app.infrastructure.cache.redis_adapter import RedisCacheAdapter


def cached(cache: RedisCacheAdapter, key_builder: Callable[..., str], ttl: int):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            key = key_builder(*args, **kwargs)
            hit = await cache.get(key)
            if hit is not None:
                return hit
            result = await fn(*args, **kwargs)
            await cache.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator