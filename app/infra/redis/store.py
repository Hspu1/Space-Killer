import logging
import time
from typing import Final

from starsessions import SessionStore
from redis.asyncio import Redis

from app.infra.redis.service import RedisService
from app.utils import Colors

logger = logging.getLogger(__name__)


class RedisSessionStore(SessionStore):
    __slots__ = ("_service", "_prefix_root")

    def __init__(
            self, service: RedisService,
            prefix: str = "session", version: str = "v1"
    ) -> None:
        self._service: Final[RedisService] = service
        self._prefix_root: Final[str] = f"{prefix}:{version}"

    def _get_key(self, sid: str) -> str:
        return f"{self._prefix_root}:{sid}"

    async def read(self, session_id: str, lifetime: int) -> bytes | None:
        client: Redis = self._service.get_client()
        start = time.perf_counter()
        result = await client.get(name=self._get_key(session_id))

        if logger.isEnabledFor(logging.DEBUG):
            dur = time.perf_counter() - start
            logger.debug(
                "%s[REDIS] READ%s sid=%s...: total %s%.4fs%s",
                Colors.PURPLE, Colors.RESET, session_id[:8],
                Colors.YELLOW, dur, Colors.RESET
            )
        return result

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        if ttl <= 0:
            await self.remove(session_id)
            return session_id

        key = self._get_key(session_id)
        client: Redis = self._service.get_client()
        start = time.perf_counter()
        await client.set(name=key, value=data, ex=ttl)

        if logger.isEnabledFor(logging.DEBUG):
            dur = time.perf_counter() - start
            logger.debug(
                "%s[REDIS] WRITE%s sid=%s..., size=%db: total %s%.4fs%s",
                Colors.PURPLE, Colors.RESET, session_id[:8], len(data),
                Colors.YELLOW, dur, Colors.RESET
            )
        return session_id

    async def remove(self, session_id: str) -> None:
        client: Redis = self._service.get_client()
        start = time.perf_counter()
        await client.delete(self._get_key(session_id))

        if logger.isEnabledFor(logging.DEBUG):
            dur = time.perf_counter() - start
            logger.debug(
                "%s[REDIS] REMOVE%s sid=%s...: total %s%.4fs%s",
                Colors.PURPLE, Colors.RESET, session_id[:8],
                Colors.YELLOW, dur, Colors.RESET
            )
