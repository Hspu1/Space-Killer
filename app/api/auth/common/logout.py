from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse


logout_router = APIRouter(tags=["common auth"])


@logout_router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()

    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": "/"})

    return RedirectResponse(url="/", status_code=303)
