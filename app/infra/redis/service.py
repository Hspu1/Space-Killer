from asyncio import Lock

from redis.asyncio import Redis, ConnectionPool

from app.core.env_conf import stg


class RedisService:
    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None
        self._lock = Lock()

    async def init_state(self, host: str, port: int, db: int) -> None:
        if self._pool or self._client:  # state already exists
            return None  # exit the function and move on

        async with self._lock:
            if self._pool or self._client:
                return None

            self._pool = ConnectionPool(  # open connections
                # (to not initialize a new one every single time)
                host=host, port=port, db=db,
                max_connections=stg.max_connections,
                socket_connect_timeout=stg.socket_connect_timeout,
                decode_responses=False  # avoiding unnecessary decoding
            )
            self._client = Redis(connection_pool=self._pool)
            await self._client.ping()

    def get_client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisService isn't initialized")
        return self._client

    async def aclose(self) -> None:
        if self._pool:
            await self._pool.disconnect()
            self._pool, self._client = None, None  # service shutdown guarantee


redis_service = RedisService()
