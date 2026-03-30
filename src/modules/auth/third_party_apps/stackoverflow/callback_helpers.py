from typing import Final
from urllib.parse import parse_qs

from curl_cffi.const import CurlHttpVersion
from curl_cffi.requests import AsyncSession
from curl_cffi.requests.exceptions import RequestException
from fastapi import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from src.core.env_conf import auth_stg, server_stg
from src.utils import log_error_auth
from src.utils.log_helpers import log_warn_auth

from ...common import AuthProvider

headers: Final[dict] = {
    "Accept": "application/json",
    "User-Agent": "Smth-P",
    "Content-Type": "application/x-www-form-urlencoded",
}
session: Final[AsyncSession] = AsyncSession(
    headers=headers,
    max_clients=10,
    verify=server_stg.ssl_check,
    timeout=auth_stg.auth_timeout,
    http_version=CurlHttpVersion.V2_0,
    impersonate="safari15_3",
)


def is_retryable(e: Exception) -> bool:
    if isinstance(e, RequestException):
        if e.response is not None:
            return (
                e.response.status_code >= HTTP_500_INTERNAL_SERVER_ERROR
                or e.response.status_code == HTTP_429_TOO_MANY_REQUESTS
            )
        return True

    return False


def log_retry(retry_state: RetryCallState) -> None:
    exc, detail = retry_state.outcome.exception(), "Unknown Error"
    try:
        if isinstance(exc, RequestException) and exc.response is not None:
            status = exc.response.status_code
            try:
                detail = f"Status: {status}, Body: {exc.response.text[:250]}"
            except Exception:
                detail = f"Status: {status} (Body is unreadable)"

    except Exception:
        detail = f"Cannnot get status and body, exc: {exc}"

    log_warn_auth(
        provider="STACKOVERFLOW",
        message=f"SO attempt {retry_state.attempt_number} failed. {detail}",
    )


do_retry = retry(
    retry=retry_if_exception(is_retryable),  # predicate
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=5),
    # multiplier=1 equals standard behaviour of the formula
    reraise=True,
    before_sleep=log_retry,
)


@do_retry
async def exchange_so_token(request, redirect_uri):
    code = request.query_params["code"]
    res = await session.post(
        url="https://stackoverflow.com/oauth/access_token",
        data={
            "client_id": auth_stg.stackoverflow_client_id,
            "client_secret": auth_stg.stackoverflow_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    res.raise_for_status()

    if "access_token" not in (data := parse_qs(res.text)):
        err_msg = f"Response missing access_token: {res.text[:100]}"
        raise ValueError(err_msg)

    if not (access_data := data["access_token"]):
        err_msg = "SO Response missing data for the access_token field"
        raise ValueError(err_msg)

    return {"access_token": access_data[0]}  # getting a single list item


async def fetch_so_user(access_token: str) -> dict:
    resp = await session.get(
        url="https://api.stackexchange.com/2.3/me",
        params={
            "site": "stackoverflow",
            "key": auth_stg.stackoverflow_api_key,
            "access_token": access_token,
        },
    )

    if resp.status_code != HTTP_200_OK:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="API fetch FAILED")
        resp.raise_for_status()

    if "backoff" in (user_data := resp.json()):
        backoff = str(user_data["backoff"])
        log_warn_auth(
            provider=AuthProvider.STACKOVERFLOW,
            message="Backoff received",
            seconds=backoff,
        )

        raise HTTPException(
            status_code=429,
            headers={"Retry-After": backoff},
        )

    items = user_data.get("items")
    if not items:
        err_msg = "User data missing items"
        raise ValueError(err_msg)

    return items[0]  # getting a single dict from the list
