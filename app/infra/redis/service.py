from asyncio import Lock

from redis.asyncio import Redis, ConnectionPool

from app.core.env_conf import stg


class RedisService:
    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None
        self._lock = Lock()

    async def init_state(self, host: str, port: int, db: int) -> None:
        if self._pool or self._client:
            return None

        async with self._lock:
            if self._pool or self._client:
                return None

            pool = ConnectionPool(  # open connections
                # (to not initialize a new one every single time)
                host=host, port=port, db=db,
                max_connections=stg.max_connections,
                socket_connect_timeout=stg.socket_connect_timeout,
                decode_responses=False  # avoiding unnecessary decoding
            )
            client = Redis(connection_pool=pool)

            try:
                await client.ping()
                self._pool, self._client = pool, client

            except Exception as e:
                await pool.disconnect()
                raise e

    def get_client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisService isn't initialized")
        return self._client

    async def aclose(self) -> None:
        if self._pool:
            await self._pool.disconnect()
            self._pool, self._client = None, None


redis_service = RedisService()
