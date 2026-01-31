from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse


logout_router = APIRouter(tags=["common auth"])


@logout_router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()

    return Response(headers={"HX-Redirect": "/"}) \
        if request.headers.get("HX-Request") \
        else RedirectResponse(url="/", status_code=303)
