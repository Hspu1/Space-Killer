from asyncio import gather, shield
from time import perf_counter

from httpx import (
    AsyncClient, Limits, Response, TimeoutException,
    NetworkError, RemoteProtocolError, HTTPStatusError
)
from tenacity import (
    retry, stop_after_attempt,
    wait_random_exponential, retry_if_exception_type
)

from app.core.env_conf import AuthSettings, ServerSettings, http_stg
from app.utils.log_helpers import log_debug_http, log_error_infra, log_warn_auth

RETRY_EXCEPTIONS = (
    TimeoutException, NetworkError,
    RemoteProtocolError, HTTPStatusError
)


class HttpService:
    __slots__ = ("_auth_stg", "_server_stg", "client")

    def __init__(self, auth_stg: AuthSettings, server_stg: ServerSettings):
        self._auth_stg, self._server_stg = auth_stg, server_stg
        self.client: AsyncClient | None = None

    async def connect(self):
        if self.client:
            return

        start = perf_counter()
        try:
            limits = Limits(
                max_connections=http_stg.max_connections,
                max_keepalive_connections=http_stg.max_keepalive_connections,
                keepalive_expiry=http_stg.keepalive_expiry
            )
            self.client = AsyncClient(
                proxy=self._server_stg.proxy, limits=limits,
                timeout=self._auth_stg.auth_timeout,
                verify=self._server_stg.ssl_check
            )
            if tasks := [self.client.get(url) for url in http_stg.warmup_urls if "127.0.0.1" not in url]:
                await gather(*tasks, return_exceptions=True)

            log_debug_http(
                op="CONNECTED", start_time=start, detail="Pools(%d, %ds keep alive %d) warmed up" % (
                    http_stg.max_connections, http_stg.keepalive_expiry, http_stg.max_keepalive_connections
                ))

        except Exception as e:
            log_error_infra(service="HTTP", op="CONNECT", exc=e)
            raise e

    @retry(
        retry=retry_if_exception_type(RETRY_EXCEPTIONS),
        stop=stop_after_attempt(3), wait=wait_random_exponential(multiplier=1, max=5),
        reraise=True, before_sleep=lambda res: log_warn_auth(  # 'res' provides methods from tenacity
            provider="HTTP", message="GITHUB Attempt %d failed, Error: %s" % (
                res.attempt_number, res.outcome.exception()
            )
        )
    )
    async def _make_request(self, method: str, url: str, **kwargs) -> Response:
        resp = await self.client.request(method, url, **kwargs)
        if resp.status_code >= 500 or resp.status_code == 429:
            resp.raise_for_status()
        return resp

    async def safe_post(self, url: str, **kwargs) -> Response:
        try:
            return await self._make_request("POST", url, **kwargs)
        except Exception as e:
            log_error_infra(service="HTTP", op="POST", exc=e)
            raise e

    async def safe_get(self, url: str, **kwargs) -> Response:
        try:
            return await self._make_request("GET", url, **kwargs)
        except Exception as e:
            log_error_infra(service="HTTP", op="GET", exc=e)
            raise e

    async def disconnect(self):
        if not self.client:
            return

        async def _do_disconnect():
            start = perf_counter()
            try:
                if self.client:
                    await self.client.aclose()
                log_debug_http(op="DISCONNECTED", start_time=start)

            except Exception as e:
                log_error_infra(service="HTTP", op="DISCONNECT", exc=e)
                raise e

            finally:
                self.client = None

        await shield(_do_disconnect())
