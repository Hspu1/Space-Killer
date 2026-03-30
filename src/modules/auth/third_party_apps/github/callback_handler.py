from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from src.infra.auth_http_client import AuthHttpClient
from src.infra.persistence.postgres import PostgresManager
from src.utils import log_debug_auth, log_error_auth

from ...common import AuthProvider, get_safe_user_info, pg_resolve_user_id
from .enums import HttpMethods
from .kwargs import github_kwargs


async def github_callback_handler(
    request: Request,
    pg_manager: PostgresManager,
    redirect_uri: str,
    auth_http_client: AuthHttpClient,
) -> RedirectResponse:

    start = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    returned_state, returned_code = (
        request.query_params.get("state", None),
        request.query_params.get("code", None),
    )
    if not returned_state or not returned_code:
        return RedirectResponse(url="/?msg=provider_error")

    saved_state = request.session.pop("state", None)
    if returned_state != saved_state:
        log_error_auth(provider=AuthProvider.GITHUB, message="CSRF state mismatch")
        return RedirectResponse(url="/?msg=session_expired")

    try:
        start_token = perf_counter()
        token_data = await exchange_github_token(
            auth_http_client, request.query_params["code"], redirect_uri
        )
        log_debug_auth(
            label="token_fetch", start_time=start_token, provider=AuthProvider.GITHUB
        )

        start_api = perf_counter()
        safe_user_info = await fetch_github_profile(
            auth_http_client, token_data["access_token"]
        )
        log_debug_auth(
            label="api_fetch", start_time=start_api, provider=AuthProvider.GITHUB
        )

        user_id = await pg_resolve_user_id(
            pg_manager=pg_manager, user_info=safe_user_info, provider=AuthProvider.GITHUB
        )

        request.session.pop("user_id", None)
        request.session.pop("given_name", None)
        request.session.update({"user_id": user_id, "given_name": safe_user_info.name})

        log_debug_auth(label="total", start_time=start, provider=AuthProvider.GITHUB)
        return RedirectResponse(url="/welcome")

    except (OAuthError, ValueError, Exception) as e:
        log_error_auth(provider=AuthProvider.GITHUB, message=str(e), exc=e)
        return RedirectResponse(url="/?msg=provider_error")


async def exchange_github_token(client: AuthHttpClient, code: str, uri: str) -> dict:
    params = github_kwargs(HttpMethods.POST, code=code, redirect_uri=uri)
    res = await client.post(**params)

    if res and "error" not in (data := res.json()):
        return data

    raise ValueError(res.text if res else "No response")


async def fetch_github_profile(client: AuthHttpClient, token: str) -> dict:
    params = github_kwargs(HttpMethods.GET, access_token=token)
    res = await client.get(**params)

    if res and "error" not in (data := res.json()):
        return get_safe_user_info(data, provider=AuthProvider.GITHUB)

    raise ValueError(res.status_code if res else "No res")
