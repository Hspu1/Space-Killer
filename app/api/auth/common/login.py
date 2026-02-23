import logging
from secrets import token_urlsafe
from time import perf_counter

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from app.api.auth.common import AuthProvider
from app.core.env_conf import auth_stg
from app.utils.logger_conf import Colors

logger = logging.getLogger(__name__)


async def login(
        request: Request, provider_name: AuthProvider,
        provider: StarletteOAuth2App
) -> Response:

    start = perf_counter()
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    redirect_uri = f"{base_url}/auth/{provider_name.value.lower()}/callback"

    if provider_name.value.lower() == "stackoverflow":
        state = token_urlsafe(32)
        request.session["so_state"] = state
        url = (
            "https://stackoverflow.com/oauth"
            "?client_id=%s&redirect_uri=%s&state=%s&scope=no_expiry"
        ) % (auth_stg.stackoverflow_client_id, redirect_uri, state)

    elif provider_name.value.lower() == "github":
        state = token_urlsafe(32)
        request.session["github_state"] = state
        url = (
            "https://github.com/login/oauth/authorize"
            "?client_id=%s&redirect_uri=%s&state=%s&scope=user:email"
        ) % (auth_stg.github_client_id, redirect_uri, state)

    else:
        provider_url = await provider.authorize_redirect(request, redirect_uri)
        url = provider_url.headers.get("location")

    if logger.isEnabledFor(logging.DEBUG):
        duration = (perf_counter() - start) * 1000
        logger.debug(
            "%s[AUTH LOGIN]%s provider=%s, total=%s%.2fms%s",
            Colors.PURPLE, Colors.RESET, provider_name.value.upper(),
            Colors.YELLOW, duration, Colors.RESET
        )

    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": url})

    return RedirectResponse(url)
