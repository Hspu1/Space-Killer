from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.core.env_conf import stg
from ..common import get_user_id, AuthProvider
from .client import stackoverflow_oauth

from curl_cffi.requests import AsyncSession
from urllib.parse import parse_qs


async def stackoverflow_callback_handling(request: Request) -> RedirectResponse:
    code = request.query_params.get("code")  # temporary unique string
    if not code or request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        async with AsyncSession() as session:
            res = await session.post(
                "https://stackoverflow.com/oauth/access_token",
                data={
                    "client_id": stg.stackoverflow_client_id,
                    "client_secret": stg.stackoverflow_client_secret, "code": code,
                    "redirect_uri": f"{request.url.scheme}://{request.url.netloc}/auth/stackoverflow/callback"
                },  # receiving an access_token in exchange for a code
                impersonate="chrome110"  # forging a TLS fingerprint
                # so that it's identical to the Chrome 110th vers (recommended)
            )

        token_dict = {k: v[0] for k, v in parse_qs(res.text).items()}  # parse_qs: str -> dict
        resp = None
        if access_token := token_dict.get("access_token"):
            resp = await stackoverflow_oauth.stackoverflow.get(
                'me',  # special SO's view
                params={'site': 'stackoverflow', 'key': stg.stackoverflow_api_key},
                token={'access_token': access_token, 'token_type': 'Bearer'}
            )

        data = resp.json()
        raw_user_info = data["items"][0]
        user_info_id = str(raw_user_info["user_id"])

        user_info = {
            "email": f"{user_info_id}@stackoverflow.user",
            "name": raw_user_info.get("display_name"),
            "email_verified": True
        }

        user_id = await get_user_id(
            user_info=user_info,
            provider=AuthProvider.STACKOVERFLOW,
            provider_user_id=user_info_id
        )
        request.session.clear()
        request.session['user_id'] = user_id
        request.session['given_name'] = user_info["name"].split()[0]

        return RedirectResponse(url='/welcome')

    except (OAuthError, Exception) as e:
        print(f"SO Error: {e}")
        return RedirectResponse(url="/?msg=session_expired")
