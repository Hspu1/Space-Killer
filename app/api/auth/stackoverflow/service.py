from urllib.parse import parse_qs

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse
from curl_cffi.requests import AsyncSession as TLSClient


from app.core.env_conf import stg
from ..common import get_user_id, AuthProvider
from .client import stackoverflow_oauth


async def stackoverflow_callback_handling(request: Request, redirect_uri: str) -> RedirectResponse:
    returned_state = request.query_params.get("state")
    saved_state = request.session.pop('so_state', None)

    if not returned_state or returned_state != saved_state:
        print(f"CSRF Alert, received: {returned_state}, expected: {saved_state}")
        return RedirectResponse(url="/?msg=session_expired")

    code = request.query_params.get("code")
    if not code or request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        async with TLSClient() as session:
            res = await session.post(
                "https://stackoverflow.com/oauth/access_token",
                data={
                    "client_id": stg.stackoverflow_client_id,
                    "client_secret": stg.stackoverflow_client_secret, "code": code,
                    "redirect_uri": redirect_uri
                },
                impersonate="chrome110"
            )
        if res.status_code != 200:
            raise OAuthError(f"SO token error: {res.status_code}")

        token_dict = {k: v[0] for k, v in parse_qs(res.text).items()}
        resp = None
        if access_token := token_dict.get("access_token"):
            resp = await stackoverflow_oauth.stackoverflow.get(
                'me',
                params={'site': 'stackoverflow', 'key': stg.stackoverflow_api_key},
                token={'access_token': access_token, 'token_type': 'Bearer'}
            )

        data = resp.json()
        raw_user_info = data["items"][0]
        user_info_id = str(raw_user_info["user_id"])

        user_info = {
            "email": f"{user_info_id}@stackoverflow.user",
            "name": raw_user_info.get("display_name")
        }

        user_id = await get_user_id(
            user_info=user_info,
            provider=AuthProvider.STACKOVERFLOW,
            provider_user_id=user_info_id
        )
        request.session.clear()
        request.session.update({
            "user_id": user_id,
            "given_name": user_info["name"].split()[0] or "SO User"
        })

        return RedirectResponse(url='/welcome')

    except (OAuthError, Exception) as e:
        print(f"SO Error: {e}")
        return RedirectResponse(url="/?msg=session_expired")
