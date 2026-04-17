from time import perf_counter
from typing import Any

from redis.asyncio import ConnectionError as RedisConnError
from redis.asyncio import Redis
from throttled.asyncio.store.redis import RedisStore

from src.core.env_conf import RedisSettings
from src.core.exceptions import RedisNotReachableError
from src.utils.log_helpers import log_debug_redis


class RedisManager:
    def __init__(self, config: RedisSettings) -> None:
        self._config = config
        self._client: Redis | None = None
        self._rate_limiter: RedisStore | None = None

    async def connect(self) -> None:
        if self._client:
            return

        start = perf_counter()
        self._client = Redis(
            host=self._config.host,
            port=self._config.port,
            db=self._config.db,
            max_connections=100,  # 100/250
            socket_connect_timeout=self._config.socket_connect_timeout,
            socket_keepalive=True,
            socket_timeout=self._config.socket_timeout,
            decode_responses=False,
            health_check_interval=self._config.health_check_interval,
        )

        try:
            await self.ping()
            log_debug_redis(
                op="CONNECTED",
                start_time=start,
                detail=f"{self._config.host}:{self._config.port}/db={self._config.db}",
            )

        except (RedisConnError, TimeoutError, Exception) as e:
            await self.disconnect()
            raise RedisNotReachableError from e

    async def ping(self) -> bool:
        if not self._client:
            raise RedisNotReachableError

        await self._client.ping()

    def get_client(self) -> Redis:
        if self._client is None:
            raise RedisNotReachableError

        return self._client

    def _get_options(self) -> dict[str, Any]:
        return {
            "max_connections": 150,  # 150/250
            "socket_timeout": self._config.socket_timeout,
            "socket_connect_timeout": self._config.socket_connect_timeout,
            "socket_keepalive": True,
            "retry_on_timeout": False,
            "decode_responses": False,
            "REUSE_CONNECTION": True,
            "PREFIX": "rl:v1:",
            "health_check_interval": self._config.health_check_interval,
        }

    def get_rate_limiter(self) -> RedisStore:
        if self._rate_limiter is None:
            self._rate_limiter = RedisStore(
                server=self._config.db_url, options=self._get_options()
            )
        return self._rate_limiter

    async def disconnect(self) -> None:
        if not self._client:
            return

        start = perf_counter()
        try:
            await self._client.aclose()
            log_debug_redis(op="DISCONNECTED", start_time=start)

        finally:
            self._client, self._rate_limiter = None, None
