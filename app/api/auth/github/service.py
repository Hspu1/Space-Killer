from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..common import get_user_id, AuthProvider
from .client import github_oauth


async def github_callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        token = await github_oauth.github.authorize_access_token(request)
        resp = await github_oauth.github.get('user', token=token)
        user_info = resp.json()
        print(f"GitHub: {user_info}")
        user_info_id = str(user_info["id"])
        user_info["email"] = f"{user_info_id}@github.user"

        user_id = await get_user_id(
            user_info=user_info,
            provider=AuthProvider.GITHUB,
            provider_user_id=user_info_id
        )
        request.session.clear()
        request.session.update({
            "user_id": user_id,
            "given_name": user_info.get("name") or user_info.get("login")
        })

        return RedirectResponse(url='/welcome')

    except OAuthError:
        return RedirectResponse(url="/?msg=session_expired")
