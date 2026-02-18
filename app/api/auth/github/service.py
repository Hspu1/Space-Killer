from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth
from ..common import get_user_id, AuthProvider, get_safe_info
from .client import github_oauth


async def github_callback_handling(
        request: Request, pg_svc: PostgresService
) -> RedirectResponse:

    start_total = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        start_token = perf_counter()
        token = await github_oauth.github.authorize_access_token(request)
        log_debug_auth(label="token_fetch", start=start_token,
                            provider=AuthProvider.GITHUB)

        start_api = perf_counter()
        resp = await github_oauth.github.get('user', token=token)
        log_debug_auth(label="api_fetch", start=start_api,
                            provider=AuthProvider.GITHUB)

        if resp.status_code != 200:
            log_error_auth(
                provider=AuthProvider.GITHUB,
                message=f"API failed status={resp.status_code} body={resp.text[:50]}"
            )
            return RedirectResponse(url="/?msg=provider_error")

        user_info = resp.json()
        safe_user_info = get_safe_info(user_info=user_info, provider=AuthProvider.GITHUB)
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info,
            provider=AuthProvider.GITHUB
        )
        request.session.clear()
        request.session.update({
            "user_id": user_id, "given_name": safe_user_info["name"]
        })

        log_debug_auth(label="total", start=start_total,
                            provider=AuthProvider.GITHUB)
        return RedirectResponse(url='/welcome')

    except OAuthError as e:
        log_error_auth(provider=AuthProvider.GITHUB, message="oauth err", exc=e)
        return RedirectResponse(url="/?msg=session_expired")

    except Exception as e:
        log_error_auth(provider=AuthProvider.GITHUB, message="unexpected", exc=e)
        return RedirectResponse(url="/?msg=provider_error")
