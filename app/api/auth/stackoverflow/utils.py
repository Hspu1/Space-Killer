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
        raise HTTPError("NO AUTH CODE provided")

    async with TLSClient() as session:
        res = await session.post(
            url=auth_stg.so_access_token_link,
            data={
                "client_id": auth_stg.stackoverflow_client_id,
                "client_secret": auth_stg.stackoverflow_client_secret,
                "code": code, "redirect_uri": redirect_uri
            }, impersonate="chrome110"
        )

    log_debug_auth(label="token_exchange", start_time=start, provider=AuthProvider.STACKOVERFLOW)
    if res.status_code != 200 or not res.text:
        raise HTTPError("TOKEN exchange FAILED: %s" % res.status_code)

    if not (parsed_data := parse_qs(res.text)):
        raise ValueError("RESPONSE is empty or INVALID format")

    if "access_token" not in parsed_data:
        raise HTTPError("RESPONSE is MISSING the ACCESS TOKEN in %s" % parsed_data)

    return {k: v[0] for k, v in parsed_data.items()}


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

    try:
        user_data = resp.json()
    except ValueError:
        raise ValueError("API returned INVAlID JSON")
    except Exception:
        raise ValueError("API returned INVAlID JSON")

    if not user_data or not isinstance(user_data, dict):
        raise ValueError("API response is INVALID")

    if "backoff" in user_data:
        log_warn_auth(provider=AuthProvider.STACKOVERFLOW, message="Backoff received", seconds=user_data["backoff"])

    if not (items := user_data.get("items")) or not isinstance(items, list):
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="User items missing in response")
        raise KeyError("Response ITEMS MISSING")

    log_debug_auth(label="api_fetch", start_time=start, provider=AuthProvider.STACKOVERFLOW)
    return user_data["items"][0]
