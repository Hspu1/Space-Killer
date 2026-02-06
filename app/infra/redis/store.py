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
        data = await self._get_conn().get(self._key(session_id)) or b""
        print(f"[READ] {len(data)} bytes")
        return data

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        print(f"[WRITE] {len(data)} bytes | ttl: {ttl}")
        await self._get_conn().set(self._key(session_id), data, ex=max(1, ttl))
        return session_id

    async def remove(self, session_id: str) -> None:
        print(f"[REMOVE] sid: {session_id}")
        await self._get_conn().delete(self._key(session_id))
