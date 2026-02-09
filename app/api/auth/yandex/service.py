from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..common import get_user_id, AuthProvider
from .client import yandex_oauth


async def yandex_callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        token = await yandex_oauth.yandex.authorize_access_token(request)
        resp = await yandex_oauth.yandex.get('info', token=token)
        raw_user_info = resp.json()
        user_info_id = str(raw_user_info["id"])

        user_info = {
            "id": user_info_id,
            "email": raw_user_info.get("default_email") or f"{user_info_id}@yandex.user",
            "name": raw_user_info.get('display_name') or raw_user_info.get('real_name'),
            "email_verified": True
        }

        user_id = await get_user_id(
            user_info=user_info,
            provider=AuthProvider.YANDEX,
            provider_user_id=user_info_id
        )
        request.session.clear()
        request.session.update({
            "user_id": user_id,
            "given_name": raw_user_info.get("first_name")
        })

        return RedirectResponse(url='/welcome')

    except OAuthError:
        return RedirectResponse(url="/?msg=session_expired")
