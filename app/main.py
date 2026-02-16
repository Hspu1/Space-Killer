from sys import argv

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from uvicorn import run
from starsessions import SessionMiddleware, SessionAutoloadMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.auth import auth_router
from app.ui import ui_router
from app.core.env_conf import server_stg, pg_stg, redis_stg
from app.core.lifespan import get_lifespan
from app.core.docs import static_docs_urls
from app.core.serializer import OrjsonSerializer
from app.infra.redis import RedisSessionStore, RedisService
from app.infra.postgres.service import PostgresService
from app.utils import setup_logging

setup_logging()


def create_app() -> FastAPI:
    pg_svc, redis_svc = (
        PostgresService(config=pg_stg), RedisService(config=redis_stg)
    )
    app = FastAPI(
        title="Smth-P", lifespan=get_lifespan(pg=pg_svc, redis=redis_svc),
        default_response_class=ORJSONResponse,
        docs_url=None, redoc_url=None,
        swagger_ui_oauth2_redirect_url="/oauth2-redirect"
    )

    static_docs_urls(app=app)

    store, serializer = RedisSessionStore(service=redis_svc), OrjsonSerializer()
    app.add_middleware(SessionAutoloadMiddleware)
    app.add_middleware(
        SessionMiddleware,
        store=store, serializer=serializer,
        cookie_name="session_id", lifetime=server_stg.session_lifetime,
        rolling=False, cookie_same_site="lax",
        cookie_https_only=True
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=server_stg.allowed_hosts)

    app.include_router(auth_router)
    app.include_router(ui_router)

    app.state.pg_svc = redis_svc
    app.state.pg_svc = redis_svc

    return app


app = create_app()

if __name__ == "__main__":
    custom_port = int(argv[1]) if len(argv) > 1 else server_stg.run_port
    # run this command: (uv run) python -m app.main <port>

    run(
        app="app.main:app", port=custom_port, host=server_stg.run_host,
        reload=server_stg.run_reload, use_colors=True, access_log=True,
        workers=1, http="httptools", loop="asyncio",
        proxy_headers=True, forwarded_allow_ips=server_stg.forwarded_ips,
    )
