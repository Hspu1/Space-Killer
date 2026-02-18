from time import perf_counter

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse
from httpx import HTTPError

from app.infra.postgres.service import PostgresService
from .utils import exchange_so_token, fetch_so_user
from app.utils import log_debug_auth, log_error_auth
from ..common import get_user_id, AuthProvider, get_safe_info


async def stackoverflow_callback_handling(
        request: Request, redirect_uri: str, pg_svc: PostgresService
) -> RedirectResponse:
    start_total = perf_counter()

    returned_state = request.query_params.get("state")
    saved_state = request.session.pop('so_state', None)
    if not returned_state or returned_state != saved_state:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="CSRF mismatch")
        return RedirectResponse(url="/?msg=session_expired")

    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        token_dict = await exchange_so_token(request=request, redirect_uri=redirect_uri)
        user_info = await fetch_so_user(access_token=token_dict["access_token"])
        safe_user_info = get_safe_info(user_info=user_info, provider=AuthProvider.STACKOVERFLOW)
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info,
            provider=AuthProvider.STACKOVERFLOW
        )

        request.session.clear()
        request.session.update({
            "user_id": user_id, "given_name": safe_user_info["name"]
        })

        log_debug_auth(label="total", start=start_total,
                            provider=AuthProvider.STACKOVERFLOW)
        return RedirectResponse(url='/welcome')

    except (HTTPError, KeyError, OAuthError) as e:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="network/provider", exc=e)
        return RedirectResponse(url="/?msg=provider_error")

    except Exception as e:
        log_error_auth(provider=AuthProvider.STACKOVERFLOW, message="unexpected", exc=e)
        return RedirectResponse(url="/?msg=provider_error")
