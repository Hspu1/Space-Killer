from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.core.env_conf import stg
from ..common import get_user_id, AuthProvider
from .client import stackoverflow_oauth


async def stackoverflow_callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        token = await stackoverflow_oauth.stackoverflow.authorize_access_token(request)
        resp = await stackoverflow_oauth.stackoverflow.get(
            'me', params={'site': 'stackoverflow', 'key': stg.stackoverflow_api_key}, token=token
        )
        data = resp.json()
        print(data)
        raw_user_info = data["items"][0]
        print(raw_user_info)
        user_info_id = str(raw_user_info["user_id"])

        user_info = {
            "email": f"{user_info_id}@stackoverflow.user",
            "name": raw_user_info.get("display_name"),
            "email_verified": True
        }

        if raw_user_info:
            request.session.clear()
            user_id = await get_user_id(
                user_info=user_info,
                provider=AuthProvider.STACKOVERFLOW,
                provider_user_id=user_info_id
            )
            request.session['user_id'] = user_id
            request.session['given_name'] = user_info["name"]

        return RedirectResponse(url='/welcome')

    except OAuthError as e:
        print(f"SO Error: {e}")
        return RedirectResponse(url="/?msg=session_expired")
