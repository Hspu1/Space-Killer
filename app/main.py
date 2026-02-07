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
from app.core.lifespan import get_lifespan
from app.core.docs import static_docs_urls
from app.core.session import OrjsonSerializer
from app.infra.redis import RedisSessionStore, redis_service, RedisService


auth_routers = (
    google_router, github_router, telegram_router,
    yandex_router, stackoverflow_router, logout_router
)
ui_routers = (homepage_router, welcome_router)


def create_app(redis_svc: RedisService = redis_service, testing: bool = False) -> FastAPI:
    """Factory for creating an application"""
    app = FastAPI(
        title="Smth-P", lifespan=get_lifespan(redis_service=redis_svc),
        default_response_class=ORJSONResponse,
        docs_url=None, redoc_url=None,
        swagger_ui_oauth2_redirect_url="/oauth2-redirect"
    )

    if testing:
        app.state.testing = True

    static_docs_urls(app=app)

    # middlewares
    store, serializer = RedisSessionStore(service=redis_svc), OrjsonSerializer()
    app.add_middleware(SessionAutoloadMiddleware)
    app.add_middleware(
        SessionMiddleware,
        store=store, serializer=serializer,
        cookie_name="session_id", lifetime=stg.session_lifetime,
        rolling=False, cookie_same_site="lax",
        cookie_https_only=True
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=stg.allowed_hosts)

    for router in (*auth_routers, *ui_routers):
        app.include_router(router)

    return app


app = create_app()

if __name__ == "__main__":
    run(
        app=app, port=stg.run_port, host=stg.run_host,
        reload=stg.run_reload, use_colors=True, access_log=False,
        workers=1, http="httptools", loop="asyncio",
        # httptools -> lightweight HTTP parser,
        proxy_headers=True, forwarded_allow_ips=stg.forwarded_ips,
    )
