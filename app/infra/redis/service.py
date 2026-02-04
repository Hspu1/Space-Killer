from redis.asyncio import Redis, ConnectionPool


class RedisService:
    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    def init_state(self, host: str, port: int, db: int):
        self._pool = ConnectionPool(  # open connections
            # (to not initialize a new one every single time)
            host=host, port=port, db=db,
            max_connections=100, socket_connect_timeout=2.0,
            decode_responses=False  # avoiding unnecessary decoding
        )
        self._client = Redis(connection_pool=self._pool)

    @property  # method -> attribute
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisService isn't initialized")
        return self._client

    async def aclose(self):
        if self._pool:
            await self._pool.disconnect()


redis_service = RedisService()
