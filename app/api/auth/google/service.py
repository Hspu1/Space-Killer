from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..common import get_user_id, AuthProvider
from .client import google_oauth


async def google_callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        token = await google_oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        user_info_id = str(user_info["sub"])
        user_info["email_verified"] = True

        if user_info:
            request.session.clear()

            user_id = await get_user_id(
                user_info=user_info,
                provider=AuthProvider.GOOGLE,
                provider_user_id=user_info_id
            )
            request.session['user_id'] = user_id
            request.session['given_name'] = user_info.get("given_name", "User")

        return RedirectResponse(url='/welcome')

    except OAuthError:
        return RedirectResponse(url="/?msg=session_expired")
