from time import perf_counter
from typing import Any, Final

from httpx import AsyncClient, HTTPStatusError, Limits, RequestError, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_500_INTERNAL_SERVER_ERROR
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from src.core.env_conf import AuthSettings, ServerSettings, http_stg
from src.core.exceptions import HttpServiceNotConnectedError
from src.utils.log_helpers import log_debug_http, log_warn_auth

limits: Final[Limits] = Limits(
    max_connections=http_stg.max_connections,
    max_keepalive_connections=http_stg.max_keepalive_connections,
    keepalive_expiry=http_stg.keepalive_expiry,
)
headers: Final[dict[str, str]] = {
    "Accept": "application/json",
    "User-Agent": "Smth-P",
    "Content-Type": "application/x-www-form-urlencoded",  # for AuthN
}


def is_retryable(e: Exception) -> bool:
    if isinstance(e, RequestError):
        return True

    if isinstance(e, HTTPStatusError):
        return (
            e.response.status_code >= HTTP_500_INTERNAL_SERVER_ERROR
            or e.response.status_code == HTTP_429_TOO_MANY_REQUESTS
        )
    return False


def log_retry(retry_state: RetryCallState) -> None:
    exc, detail = retry_state.outcome.exception(), "Unknown Error"
    if isinstance(exc, HTTPStatusError):
        status = exc.response.status_code
        try:
            detail = f"Status: {status}, Body: {exc.response.text[:250]}"
        except Exception:
            detail = f"Status: {status} (Body is unreadable)"
    elif exc:
        detail = f"Cannnot get status and body, exc: {exc}"

    log_warn_auth(
        provider="HTTP",
        message=f"DOLBAYEB attempt {retry_state.attempt_number} failed. Detail: {detail}",
    )


do_retry: Final = retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=5),
    reraise=True,
    before_sleep=log_retry,
)


class AuthHttpClient:
    def __init__(self, auth_stg: AuthSettings, server_stg: ServerSettings):
        self._auth_stg, self._server_stg = auth_stg, server_stg
        self._client: AsyncClient | None = None

    async def connect(self):
        if self._client:
            return

        start = perf_counter()
        try:
            self._client = AsyncClient(
                headers=headers,
                # proxy=self._server_stg.proxy,
                limits=limits,
                timeout=self._auth_stg.auth_timeout,
                verify=self._server_stg.ssl_check,
                # http2=True,
            )

            log_debug_http(
                op="CONNECTED",
                start_time=start,
                detail=(
                    f"Pools({http_stg.max_connections}, {http_stg.keepalive_expiry}s "
                    f"keep alive {http_stg.max_keepalive_connections})"
                ),
            )

        except Exception as e:
            await self.disconnect()
            raise HttpServiceNotConnectedError from e

    async def ping(self):
        if not self._client:
            raise HttpServiceNotConnectedError

        try:
            resp = await self._client.request("HEAD", url="https://github.com")
            if resp.status_code >= 500:
                raise RuntimeError(
                    f"AuthHttpClient server error while tryna ping: {resp.status_code}"
                )

        except Exception as e:
            print(f"AuthHttpClient ping failed, err: {e}", flush=True)
            raise

    @do_retry
    async def _make_request(self, method: str, url: str, **kwargs: Any) -> Response:
        if not self._client:
            raise HttpServiceNotConnectedError

        resp = await self._client.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self._make_request("POST", url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self._make_request("GET", url, **kwargs)

    async def disconnect(self):
        if not self._client:
            return

        start = perf_counter()
        try:
            await self._client.aclose()
            log_debug_http(op="DISCONNECTED", start_time=start)

        finally:
            self._client = None
