from asyncio import wait_for, TimeoutError as AsyncTimeoutError
import logging
from time import perf_counter

from redis.asyncio import (
    Redis, ConnectionError as RedisConnError,
    TimeoutError as RedisTimeoutError
)

from app.core.env_conf import RedisSettings
from app.utils import Colors

logger = logging.getLogger(__name__)


class RedisService:
    __slots__ = ("_config", "_client")

    def __init__(self, config: RedisSettings) -> None:
        self._config = config
        self._client: Redis | None = None

    async def connect(self) -> None:
        if self._client:
            return

        start = perf_counter()
        self._client = Redis(
            host=self._config.host, port=self._config.port,
            db=self._config.db, max_connections=self._config.max_connections,
            socket_connect_timeout=self._config.socket_connect_timeout,
            decode_responses=False,
            health_check_interval=self._config.health_check_interval,
        )

        try:
            await wait_for(self._client.ping(), timeout=3.0)

        except (RedisConnError, AsyncTimeoutError, RedisTimeoutError) as e:
            await self.disconnect()
            raise ConnectionError("Redis is not reachable") from e

        if logger.isEnabledFor(logging.DEBUG):
            dur_ms = (perf_counter() - start) * 1000
            logger.debug(
                "%s[REDIS] CONNECTED%s %s:%d (db=%d): total %s%.2fms%s",
                Colors.PURPLE, Colors.RESET, self._config.host, self._config.port,
                self._config.db, Colors.YELLOW, dur_ms, Colors.RESET
            )

    def get_client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisService isn't initialized")

        return self._client

    async def disconnect(self) -> None:
        if self._client:
            start = perf_counter()
            await self._client.close()
            self._client = None

            if logger.isEnabledFor(logging.DEBUG):
                dur_ms = (perf_counter() - start) * 1000
                logger.debug(
                    "%s[REDIS] DISCONNECTED%s: total %s%.2fms%s",
                    Colors.PURPLE, Colors.RESET, Colors.YELLOW, dur_ms, Colors.RESET
                )
