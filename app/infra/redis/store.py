import logging
from time import perf_counter

from starsessions import SessionStore
from redis.asyncio import Redis

from app.infra.redis.service import RedisService
from app.utils import Colors

logger = logging.getLogger(__name__)


class RedisSessionStore(SessionStore):
    __slots__ = ("_service", "_prefix")

    def __init__(self, service: RedisService, prefix: str = "session:v1") -> None:
        self._service, self._prefix = service, prefix

    def _get_key(self, sid: str) -> str:
        return f"{self._prefix}:{sid}"

    async def read(self, session_id: str, lifetime: int) -> bytes | None:
        client: Redis = self._service.get_client()
        start = perf_counter()
        result = await client.get(name=self._get_key(session_id))

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (perf_counter() - start) * 1000
            logger.debug(
                "%s[REDIS] READ%s sid=%s...: total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET, session_id[:8],
                Colors.YELLOW, dur_ms, Colors.RESET
            )
        return result

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        client: Redis = self._service.get_client()
        key = self._get_key(sid=session_id)
        start = perf_counter()

        if ttl <= 0:
            await self.remove(session_id=session_id)
            return session_id

        await client.set(name=key, value=data, ex=ttl)

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (perf_counter() - start) * 1000
            logger.debug(
                "%s[REDIS] WRITE%s sid=%s..., size=%db: total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET, session_id[:8], len(data),
                Colors.YELLOW, dur_ms, Colors.RESET
            )
        return session_id

    async def remove(self, session_id: str) -> None:
        client: Redis = self._service.get_client()
        start = perf_counter()
        await client.delete(self._get_key(session_id))

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (perf_counter() - start) * 1000
            logger.debug(
                "%s[REDIS] REMOVE%s sid=%s...: total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET, session_id[:8],
                Colors.YELLOW, dur_ms, Colors.RESET
            )
