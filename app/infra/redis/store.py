from starsessions import SessionStore

from .service import redis_service


class LazyRedisStore(SessionStore):
    def __init__(self, prefix: str = "session"):
        self.prefix = prefix

    @property
    def connection(self):
        return redis_service.client

    def _key(self, sid: str, p: str) -> str:
        return f"{self.prefix}:{sid}:{p}"

    async def read(self, session_id: str, lifetime: int) -> bytes:
        p = self.connection.pipeline()
        p.get(self._key(session_id, "data"))
        p.exists(self._key(session_id, "invalid"))
        val, inv = await p.execute()
        return val if val and not inv else b""

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        await self.connection.set(self._key(session_id, "data"), data, ex=max(1, ttl))
        return session_id

    async def remove(self, session_id: str) -> None:
        await self.connection.delete(self._key(session_id, "data"))
        await self.connection.set(self._key(session_id, "invalid"), b"1", ex=3600)

    async def exists(self, session_id: str) -> bool:
        p = self.connection.pipeline()
        p.exists(self._key(session_id, "data"))
        p.exists(self._key(session_id, "invalid"))
        has_d, has_i = await p.execute()
        return bool(has_d and not has_i)
