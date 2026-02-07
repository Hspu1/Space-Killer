from starsessions import SessionStore

from .service import redis_service


class LazyRedisStore(SessionStore):
    def __init__(self, prefix: str = "session", salt: str = "v1"):
        self.prefix = f"{prefix}:{salt}"
        self._conn = None

    def _get_conn(self):
        if not self._conn:
            self._conn = redis_service.client
        return self._conn

    def _key(self, sid: str) -> str:
        return f"{self.prefix}:{sid}"

    async def read(self, session_id: str, lifetime: int) -> bytes:
        return await self._get_conn().get(self._key(session_id)) or b""

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        await self._get_conn().set(self._key(session_id), data, ex=max(1, ttl))
        return session_id

    async def remove(self, session_id: str) -> None:
        await self._get_conn().delete(self._key(session_id))
