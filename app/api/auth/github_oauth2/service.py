from fastapi import Request
from fastapi.responses import RedirectResponse

from app.api.auth.github_oauth2.client import github_oauth


async def github_callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    token = await github_oauth.github.authorize_access_token(request)
    user_resp = await github_oauth.github.get('user', token=token)

    print(user_resp.json())
