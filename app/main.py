from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.openapi.docs import (
    get_redoc_html, get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from uvicorn import run
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.auth import (
    github_router, google_router,
    telegram_router, yandex_router,
    stackoverflow_router, logout_router
)
from app.frontend import homepage_router, welcome_router
from app.core.env_conf import stg
from app.core.lifespan import lifespan


def static_docs_urls(app: FastAPI):
    # статика через более стабильный unpkg
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
        title="Smth-P", lifespan=lifespan,
        default_response_class=ORJSONResponse,
        docs_url=None, redoc_url=None,
        swagger_ui_oauth2_redirect_url="/oauth2-redirect"
    )

    if testing:
        app.state.testing = True

    static_docs_urls(app=app)

    # middlewares
    app.add_middleware(
        SessionMiddleware, secret_key=stg.session_secret_key,
        max_age=2592000, same_site="none", https_only=True,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    # backend - auth
    app.include_router(google_router)
    app.include_router(github_router)
    app.include_router(telegram_router)
    app.include_router(yandex_router)
    app.include_router(stackoverflow_router)
    app.include_router(logout_router)

    # frontend
    app.include_router(homepage_router)
    app.include_router(welcome_router)

    return app


app = create_app()

if __name__ == "__main__":
    run(
        app="app.main:app", port=8000,
        host="127.0.0.1", reload=False, use_colors=True,
        proxy_headers=True, forwarded_allow_ips="*"
    )
