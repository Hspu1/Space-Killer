from time import perf_counter, time
from typing import Final

from app.infra.redis import RedisService
from app.utils.log_helpers import (
    log_warn_auth, log_error_infra, log_debug_limiter
)

GCRA_LUA: Final = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local interval = tonumber(ARGV[2])
local burst = tonumber(ARGV[3])

local tat = tonumber(redis.call('GET', key)) or now
local earliest_time = tat - burst

if now >= earliest_time then
    local new_tat = math.max(tat, now) + interval
    redis.call('SET', key, new_tat, 'PX', math.ceil(new_tat - now))
    return 0
else
    return math.ceil(earliest_time - now)
end
"""


class RateLimiter:
    __slots__ = ("_redis", "_sha")

    def __init__(self, redis_svc: RedisService):
        self._redis = redis_svc
        self._sha: str | None = None

    async def init(self) -> None:
        self._sha = await self._redis.get_client().script_load(GCRA_LUA)

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        start, client = perf_counter(), self._redis.get_client()
        now_ms, interval, burst = (
            int(time() * 1000), (window * 1000) // limit, window * 1000
        )
        try:
            wait_time = await client.evalsha(
                self._sha, 1, "rate_limiter:%s" % key,
                now_ms, interval, burst
            )

            if wait_time == 0:
                log_debug_limiter(
                    op="CHECK", start_time=start, detail="key=%s res=OK" % key
                )
                return True

            log_warn_auth(
                provider="LIMITER", message="REJECTED",
                key=key, wait_ms=wait_time
            )
            return False

        except Exception as e:
            log_error_infra(service="REDIS", op="GCRA_FAIL", exc=e)
            return True
