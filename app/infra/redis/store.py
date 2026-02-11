import time
from typing import Final

from starsessions import SessionStore

from app.infra.redis.service import RedisService


class RedisSessionStore(SessionStore):
    def __init__(
            self, service: RedisService,
            prefix: str = "session", version: str = "v1"
    ) -> None:
        self._service: Final[RedisService] = service
        self._prefix_root: Final[str] = f"{prefix}:{version}"

    def _get_key(self, sid: str) -> str:
        return f"{self._prefix_root}:{sid}"

    async def read(self, session_id: str, lifetime: int) -> bytes | None:
        start = time.perf_counter()
        client = self._service.get_client()
        result = await client.get(name=self._get_key(session_id))
        print(f"[REDIS] READ sid={session_id[:8]}: {(time.perf_counter() - start):.4f}s")
        return result if result else None

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        start = time.perf_counter()
        key, client = self._get_key(session_id), self._service.get_client()
        if ttl <= 0:
            await self.remove(session_id)
            return session_id

        await client.set(name=key, value=data, ex=ttl)
        print(f"[REDIS] WRITE sid={session_id[:8]}, size={len(data)}b: {(time.perf_counter() - start):.4f}s")
        return session_id

    async def remove(self, session_id: str) -> None:
        start = time.perf_counter()
        client = self._service.get_client()
        await client.delete(self._get_key(session_id))
        print(f"[REDIS] REMOVE sid={session_id[:8]}: {(time.perf_counter() - start):.4f}s")
