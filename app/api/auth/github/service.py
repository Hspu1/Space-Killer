from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.infra.http import HttpService
from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth
from .scheme import HttpMethods
from .utils import github_kwargs
from ..common import get_user_id, AuthProvider, get_safe_info


async def github_callback_handling(
        request: Request, pg_svc: PostgresService, redirect_uri: str, http_svc: HttpService
) -> RedirectResponse:

    start = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    returned_state = request.query_params.get("state")
    saved_state = request.session.pop("github_state", None)
    if not saved_state or returned_state != saved_state:
        log_error_auth(provider=AuthProvider.GITHUB, message="CSRF state mismatch")
        return RedirectResponse(url="/?msg=session_expired")

    try:
        token_data = await exchange_github_token(http_svc, request.query_params.get('code'), redirect_uri)
        safe_user_info = await fetch_github_profile(http_svc, token_data["access_token"])
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info,
            provider=AuthProvider.GITHUB
        )

        request.session.clear()
        request.session.update({
            "user_id": user_id, "given_name": safe_user_info["name"]
        })

        log_debug_auth(label="total", start_time=start, provider=AuthProvider.GITHUB)
        return RedirectResponse(url='/welcome')

    except (OAuthError, ValueError, Exception) as e:
        log_error_auth(provider=AuthProvider.GITHUB, message="oauth err or unexpected", exc=e)
        return RedirectResponse(url="/?msg=provider_error")


async def exchange_github_token(svc, code, uri):
    params = github_kwargs(HttpMethods.POST, code=code, redirect_uri=uri)
    res = await svc.safe_post(**params)

    if "error" in (data := res.json()):
        raise ValueError("GitHub returned error: %s" % data.get("error"))
    return data


async def fetch_github_profile(svc, token):
    params = github_kwargs(HttpMethods.GET, access_token=token)
    res = await svc.safe_get(**params)

    return get_safe_info(res.json(), provider=AuthProvider.GITHUB)
