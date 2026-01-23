from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.openapi.docs import (
    get_redoc_html, get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from uvicorn import run
from starlette.middleware.sessions import SessionMiddleware

from app.frontend import homepage_router, welcome_router
from app.api.auth.google_oauth2 import google_oauth2_router
from app.core.env_conf import stg


def static_docs_urls(app: FastAPI):
    # wb statics in base.html
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="https://unpkg.com/redoc@2/bundles/redoc.standalone.js",
        )


def create_app(testing: bool = False) -> FastAPI:
    """Фабрика для создания приложения"""
    app = FastAPI(
        title="Smth-P",
        default_response_class=ORJSONResponse,
        docs_url=None, redoc_url=None,
        swagger_ui_oauth2_redirect_url="/oauth2-redirect"
    )

    if testing:
        app.state.testing = True

    static_docs_urls(app=app)

    app.add_middleware(
        SessionMiddleware,
        secret_key=stg.session_secret_key,
        same_site="lax", max_age=2592000
    )

    app.include_router(google_oauth2_router)

    app.include_router(homepage_router)
    app.include_router(welcome_router)

    return app


app = create_app()


if __name__ == "__main__":
    run(
        app="app.main:app", port=8000,
        host="127.0.0.1", reload=False, use_colors=True
    )
# local https:
# install mkcret (eg choco install mkcert)
# mkcert -install
# cd <path 2da proj>
# mkcert localhost 127.0.0.1
# uvicorn.run:
# ssl_keyfile=r"<path 2da proj>localhost+1-key.pem",
# ssl_certfile=r"<path 2da proj>localhost+1.pem"
# well done
