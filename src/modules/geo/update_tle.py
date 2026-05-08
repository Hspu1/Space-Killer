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
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
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

# Final, tuple etc
TLE_GROUPS = [
    # "kuiper",
    # "qianfan",
    # "geo",
    # "oneweb",
    "starlink"
]
