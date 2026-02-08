from secrets import token_urlsafe

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from app.core.env_conf import auth_stg


async def login(
        request: Request, provider_name: str,
        provider: StarletteOAuth2App
) -> Response:

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    redirect_uri = f"{base_url}/auth/{provider_name}/callback"

    if provider_name == "stackoverflow":
        state = token_urlsafe(32)
        request.session["so_state"] = state

        url = (
            f"https://stackoverflow.com/oauth"
            f"?client_id={auth_stg.stackoverflow_client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope=no_expiry"
        )

    else:
        provider_url = await provider.authorize_redirect(request, redirect_uri)
        url = provider_url.headers.get("location")

    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": url})

    return RedirectResponse(url)
