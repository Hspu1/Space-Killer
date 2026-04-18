from secrets import token_urlsafe
from time import perf_counter
from urllib.parse import urljoin

from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from yarl import URL

from src.core.env_conf import auth_stg
from src.utils.log_helpers import log_debug_login, log_error_auth

from .mappers import AuthProvider


async def login(
    request: Request, provider: AuthProvider, oauth_app: StarletteOAuth2App | None = None
) -> Response:

    start, provider_name = perf_counter(), provider.value
    state = token_urlsafe(32)
    request.session["state"] = state

    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    redirect_uri = f"https://{host}/auth/{provider_name.lower()}/callback"
    match provider_name.lower():
        case "stackoverflow":
            params = {
                "client_id": auth_stg.stackoverflow_client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": "no_expiry",
            }
            url = str(URL("https://stackoverflow.com/oauth").with_query(params))

        case "github":
            params = {
                "client_id": auth_stg.github_client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "scope": "user:email",
            }
            url = str(URL("https://github.com/login/oauth/authorize").with_query(params))

        case "yandex" | "google" if oauth_app is not None:
            provider_url = await oauth_app.authorize_redirect(request, redirect_uri)
            url = provider_url.headers.get("location")

        case _:
            log_error_auth(
                provider=provider_name,
                message="Attempt to login via unsupported provider",
            )
            return RedirectResponse(url="/?msg=provider_error")

    log_debug_login(start_time=start, provider=provider_name.upper())
    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": url})

    return RedirectResponse(url)
