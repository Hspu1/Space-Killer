from time import perf_counter

from starsessions import SessionStore
from redis.asyncio import Redis

from app.infra.redis.service import RedisService
from app.utils.log_helpers import log_debug_redis, log_error_infra


class RedisSessionStore(SessionStore):
    __slots__ = ("_service", "_prefix")

    def __init__(self, service: RedisService, prefix: str = "session:v1") -> None:
        self._service, self._prefix = service, prefix

    def _get_key(self, sid: str) -> str:
        return f"{self._prefix}:{sid}"

    async def read(self, session_id: str, lifetime: int) -> bytes | None:
        client: Redis = self._service.get_client()
        try:
            start = perf_counter()
            result = await client.get(name=self._get_key(session_id))

            log_debug_redis(
                op="READ session", start_time=start,
                detail=f"sid={session_id[:8]}.."
            )
            return result
        except Exception as e:
            log_error_infra(service="REDIS", op="READ session", exc=e)
            return None

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        start = perf_counter()
        try:
            if ttl <= 0:
                await self.remove(session_id=session_id)
                return session_id

            client: Redis = self._service.get_client()
            key = self._get_key(sid=session_id)
            await client.set(name=key, value=data, ex=ttl)

            log_debug_redis(
                op="WRITE session", start_time=start,
                detail=f"sid={session_id[:8]}.. size={len(data)}b"
            )
            return session_id
        except Exception as e:
            log_error_infra(service="REDIS", op="WRITE session", exc=e)
            raise e

    async def remove(self, session_id: str) -> None:
        start = perf_counter()
        try:
            client: Redis = self._service.get_client()
            await client.delete(self._get_key(session_id))
            log_debug_redis(
                op="REMOVE session", start_time=start,
                detail=f"sid={session_id[:8]}.."
            )
        except Exception as e:
            log_error_infra(service="REDIS", op="REMOVE session", exc=e)
