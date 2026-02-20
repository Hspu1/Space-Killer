from asyncio import wait_for, shield, TimeoutError as AsyncTimeoutError
from time import perf_counter

from redis.asyncio import (
    Redis, ConnectionError as RedisConnError,
    TimeoutError as RedisTimeoutError
)

from app.core.env_conf import RedisSettings
from app.utils.log_helpers import log_debug_redis, log_error_infra


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
            log_debug_redis(
                op="CONNECTED", start_time=start,
                detail=f"{self._config.host}:{self._config.port}/db={self._config.db}"
            )

        except (RedisConnError, AsyncTimeoutError, RedisTimeoutError) as e:
            await self.disconnect()
            log_error_infra(service="REDIS", op="CONNECT", exc=e)
            raise ConnectionError("Redis is not reachable") from e

        except Exception as e:
            log_error_infra(service="REDIS", op="CONNECT", exc=e)

    def get_client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisService isn't initialized")

        return self._client

    async def disconnect(self) -> None:
        if not self._client:
            return

        async def _do_disconnect():
            start = perf_counter()
            try:
                await self._client.close()
                log_debug_redis(op="DISCONNECTED", start_time=start)
            except Exception as e:
                log_error_infra("REDIS", "DISCONNECT", e)
            finally:
                self._client = None

        await shield(_do_disconnect())
