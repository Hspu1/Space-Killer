from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client.apps import StarletteOAuth2App


async def login(
        request: Request, provider_name: str,
        provider: StarletteOAuth2App
) -> Response:

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    if "loca.lt" in base_url:
        base_url = base_url.replace("http://", "https://")
    redirect_uri = f"{base_url}/auth/{provider_name}/callback"

    provider_url = await provider.authorize_redirect(request, redirect_uri)
    url = provider_url.headers.get("location")

    return Response(headers={"HX-Redirect": url}) \
        if request.headers.get("HX-Request") else RedirectResponse(url)
