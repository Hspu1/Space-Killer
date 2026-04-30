from typing import Final

from httpx import (
    AsyncClient,
    HTTPStatusError,
    Limits,
    RequestError,
)
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_500_INTERNAL_SERVER_ERROR
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from src.core.env_conf import auth_stg, http_stg, server_stg
from src.utils.log_helpers import log_warn_auth

from .base_satellite import BaseSatellite


limits: Final[Limits] = Limits(
    max_connections=http_stg.max_connections,
    max_keepalive_connections=http_stg.max_keepalive_connections,
    keepalive_expiry=http_stg.keepalive_expiry,
)
client: Final[AsyncClient] = AsyncClient(
    # proxy=server_stg.proxy,
    limits=limits,
    timeout=auth_stg.auth_timeout,
    verify=server_stg.ssl_check,
)
headers: Final[dict[str, str]] = {
    "Accept": "text/plain",
    "User-Agent": "Smth-P",
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
        provider="HTTP-PRACTIECE",
        message=f"COORDS attempt {retry_state.attempt_number} failed. Detail: {detail}",
    )


do_retry: Final = retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=5),
    reraise=True,
    before_sleep=log_retry,
)


@do_retry
async def update_tle(sat_obj: BaseSatellite) -> None:
    url = (
        f"https://celestrak.org/NORAD/elements/gp.php?CATNR={sat_obj.norad_id}&FORMAT=tle"
    )

    response = await client.get(url=url, headers=headers)
    response.raise_for_status()

    lines = response.text.strip().splitlines()
    if len(lines) >= 3:
        sat_obj.set_tle(lines[1], lines[2])
