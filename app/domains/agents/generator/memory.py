import asyncio
from collections import defaultdict


class GeneratorMemory:
    """Isolated from EvaluatorMemory. Namespaced per session."""

    def __init__(self, max_entries: int = 32):
        self._max = max_entries
        self._data: dict[str, list[dict]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def record(self, session_id: str, entry: dict) -> None:
        async with self._lock:
            self._data[session_id].append(entry)
            if len(self._data[session_id]) > self._max:
                self._data[session_id] = self._data[session_id][-self._max:]

    async def recent(self, session_id: str, n: int = 5) -> list[dict]:
        async with self._lock:
            return list(self._data[session_id][-n:])

    async def clear(self, session_id: str) -> None:
        async with self._lock:
            self._data.pop(session_id, None)