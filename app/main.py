from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from uvicorn import run
from starsessions import SessionMiddleware, SessionAutoloadMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.auth import (
    github_router, google_router,
    telegram_router, yandex_router,
    stackoverflow_router, logout_router
)
from app.frontend import homepage_router, welcome_router
from app.core.env_conf import stg
from app.core.lifespan import lifespan
from app.core.session import OrjsonSerializer
from app.core.docs import static_docs_urls
from app.infra.redis import LazyRedisStore


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
    app.add_middleware(SessionAutoloadMiddleware)
    app.add_middleware(
        SessionMiddleware,
        store=LazyRedisStore(),
        serializer=OrjsonSerializer(),
        cookie_name="session_id", lifetime=stg.session_lifetime,
        rolling=True, cookie_same_site="lax",
        cookie_https_only=True
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=stg.allowed_hosts)

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
        app="app.main:app", port=stg.run_port,
        host=stg.run_host, reload=stg.run_reload, use_colors=True,
        proxy_headers=True, forwarded_allow_ips=stg.forwarded_ips
    )
