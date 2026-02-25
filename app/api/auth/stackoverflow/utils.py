from time import perf_counter
from urllib.parse import parse_qs

from curl_cffi.requests import AsyncSession as TLSClient
from httpx import HTTPError

from app.core.env_conf import auth_stg
from app.utils import log_debug_auth, log_error_auth
from app.utils.log_helpers import log_warn_auth
from ..common import AuthProvider
from .client import stackoverflow_oauth


async def exchange_so_token(request, redirect_uri):
    start, code = perf_counter(), request.query_params.get("code")
    if not code:
        raise HTTPError("NO auth code provided")

    async with TLSClient() as session:
        res = await session.post(
            url=auth_stg.so_access_token_link,
            data={
                "client_id": auth_stg.stackoverflow_client_id,
                "client_secret": auth_stg.stackoverflow_client_secret,
                "code": code, "redirect_uri": redirect_uri
            }, impersonate="safari15_5"
        )

    log_debug_auth(label="token_exchange", start_time=start, provider=AuthProvider.STACKOVERFLOW)
    if res.status_code != 200 or not res.text:
        raise HTTPError("TOKEN exchange FAILED: %s" % res.status_code)

    return {k: v[0] for k, v in parse_qs(res.text).items()}


async def fetch_so_user(access_token: str) -> dict:
    start = perf_counter()
    resp = await stackoverflow_oauth.stackoverflow.get(
        'me',
        params={'site': 'stackoverflow', 'key': auth_stg.stackoverflow_api_key},
        token={'access_token': access_token, 'token_type': 'Bearer'}
    )

    if resp.status_code != 200:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="API fetch FAILED")
        resp.raise_for_status()

    if "backoff" in (user_data := resp.json()):
        log_warn_auth(
            provider=AuthProvider.STACKOVERFLOW,
            message="Backoff received", seconds=user_data["backoff"]
        )

    log_debug_auth(label="api_fetch", start_time=start, provider=AuthProvider.STACKOVERFLOW)
    return user_data["items"][0]
