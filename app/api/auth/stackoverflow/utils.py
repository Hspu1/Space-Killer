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
    async with TLSClient() as session:
        res = await session.post(
            "https://stackoverflow.com/oauth/access_token",
            data={
                "client_id": auth_stg.stackoverflow_client_id,
                "client_secret": auth_stg.stackoverflow_client_secret,
                "code": code, "redirect_uri": redirect_uri
            }, impersonate="chrome110"
        )

    log_debug_auth(label="token_exchange", start=start, provider=AuthProvider.STACKOVERFLOW)
    if res.status_code != 200:
        raise HTTPError(f"SO Token exchange failed: {res.status_code}")

    return {k: v[0] for k, v in parse_qs(res.text).items()}


async def fetch_so_user(access_token: str) -> dict:
    start_api = perf_counter()
    resp = await stackoverflow_oauth.stackoverflow.get(
        'me',
        params={'site': 'stackoverflow', 'key': auth_stg.stackoverflow_api_key},
        token={'access_token': access_token, 'token_type': 'Bearer'}
    )

    if resp.status_code != 200:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="API fetch failed")
        resp.raise_for_status()
    log_debug_auth(label="api_fetch", start=start_api, provider=AuthProvider.STACKOVERFLOW)

    user_data = resp.json()
    if "backoff" in user_data:
        log_warn_auth(provider="SO", message="Backoff received", seconds=user_data["backoff"])

    if not user_data.get("items"):
        raise KeyError("SO Response items missing")

    return user_data["items"][0]
