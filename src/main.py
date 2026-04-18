from sys import argv

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse, RedirectResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starsessions import SessionAutoloadMiddleware, SessionMiddleware
from uvicorn import run

from src.core.env_conf import auth_stg, pg_stg, redis_stg, server_stg
from src.core.lifespan import get_lifespan
from src.infra.auth_http_client import AuthHttpClient
from src.infra.persistence.postgres import PostgresManager
from src.infra.redis import RedisManager
from src.infra.serializer import OrjsonSerializer
from src.infra.session_store import RedisSessionStore
from src.modules.auth import auth_router
from src.ui import ui_router
from src.utils import setup_logging

from .docs import static_docs_urls
from .health import health_router

setup_logging()


def create_app() -> FastAPI:
    pg_manager, redis_manager, auth_http_client = (
        PostgresManager(config=pg_stg),
        RedisManager(config=redis_stg),
        AuthHttpClient(auth_stg=auth_stg, server_stg=server_stg),
    )

    app = FastAPI(
        title="Smth-P",
        lifespan=get_lifespan(
            pg_manager=pg_manager,
            redis_manager=redis_manager,
            auth_http_client=auth_http_client,
        ),
        default_response_class=ORJSONResponse,
        docs_url=None,
        redoc_url=None,
        swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    )

    static_docs_urls(app=app)

    store, serializer = RedisSessionStore(manager=redis_manager), OrjsonSerializer()
    app.add_middleware(SessionAutoloadMiddleware)
    app.add_middleware(
        SessionMiddleware,
        store=store,
        serializer=serializer,
        cookie_name="sid",
        lifetime=server_stg.session_lifetime,
        rolling=False,
        cookie_same_site="lax",
        # cookie_https_only=True,
    )
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=server_stg.allowed_hosts)

    app.include_router(auth_router)
    app.include_router(ui_router)
    app.include_router(health_router)

    return app


app = create_app()


@app.exception_handler(HTTP_429_TOO_MANY_REQUESTS)
async def rate_limit_handler(request: Request, exc: HTTPException) -> Response:
    wait_time = getattr(exc, "headers", {}).get("Retry-After", "a few")
    url = f"/?msg=too_many_requests&wait={wait_time}"

    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": url})

    return RedirectResponse(url)


if __name__ == "__main__":
    # RUN: (uv run) python -m app.main <port>
    # LT:  npx localtunnel --port <port> --subdomain <name>

    custom_port = int(argv[1]) if len(argv) > 1 else server_stg.run_port
    run(
        app=app,
        port=custom_port,
        host=server_stg.run_host,
        reload=False,
        use_colors=True,
        access_log=False,
        workers=1,
        http="httptools",
        loop="asyncio",
        proxy_headers=True,
        forwarded_allow_ips=server_stg.forwarded_ips,
    )
