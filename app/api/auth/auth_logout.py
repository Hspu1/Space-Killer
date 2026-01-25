from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse


auth_logout_router = APIRouter()


@auth_logout_router.post("/logout")
async def logout(request: Request) -> Response:
    request.session.clear()

    return Response(headers={"HX-Location": "/"}) \
        if request.headers.get("HX-Request") \
        else RedirectResponse(url="/", status_code=303)
