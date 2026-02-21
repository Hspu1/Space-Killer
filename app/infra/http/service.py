from asyncio import gather, shield
from time import perf_counter

from httpx import AsyncClient, Limits, Response, RemoteProtocolError, WriteError

from app.core.env_conf import AuthSettings, ServerSettings, http_stg
from app.utils.log_helpers import log_debug_net, log_error_infra, log_warn_auth


class HttpService:
    __slots__ = ("_auth_stg", "_server_stg", "client")

    def __init__(self, auth_stg: AuthSettings, server_stg: ServerSettings):
        self._auth_stg, self._server_stg = auth_stg, server_stg
        self.client: AsyncClient | None = None

    async def connect(self):
        if self.client:
            return

        start = perf_counter()
        try:
            limits = Limits(
                max_connections=http_stg.max_connections,
                max_keepalive_connections=http_stg.max_keepalive_connections,
                keepalive_expiry=http_stg.keepalive_expiry
            )
            self.client = AsyncClient(
                proxy=self._server_stg.proxy, limits=limits,
                timeout=self._auth_stg.auth_timeout,
                verify=self._server_stg.ssl_check
            )
            warmup_urls = (
                'https://github.com/login/oauth/access_token',
                'https://github.com/login/oauth/authorize',
                'https://api.github.com/user',
            )
            tasks = [self.client.get(url) for url in warmup_urls if "127.0.0.1" not in url]
            if tasks:
                await gather(*tasks, return_exceptions=True)
            log_debug_net(
                op="CONNECTED", start_time=start,
                detail="Pools(%d, %ds keep alive %d) warmed up; "
                       "URLS -> github -> access_token + authorize + api_base" % (
                    http_stg.max_connections, http_stg.keepalive_expiry,
                    http_stg.max_keepalive_connections
                )
            )

        except Exception as e:
            log_error_infra(service="HTTP", op="CONNECT", exc=e)

    async def safe_post(self, url: str, **kwargs) -> Response:
        try:
            return await self.client.post(url=url, **kwargs)
        except (RemoteProtocolError, WriteError) as e:
            log_warn_auth(
                provider="[NET/HTTP]", message="GITHUB Socket reset/error, retrying POST...",
                error=type(e).__name__
            )
            return await self.client.post(url=url, **kwargs)

    async def safe_get(self, url: str, **kwargs) -> Response:
        try:
            return await self.client.get(url=url, **kwargs)
        except (RemoteProtocolError, WriteError) as e:
            log_warn_auth(
                provider="[NET/HTTP]", message="GITHUB Socket reset/error, retrying GET...",
                error=type(e).__name__
            )
            return await self.client.get(url=url, **kwargs)

    async def disconnect(self):
        if not self.client and not self.so_session:
            return

        async def _do_disconnect():
            start = perf_counter()
            try:
                if self.client:
                    await self.client.aclose()
                if self.so_session:
                    await self.so_session.close()
                log_debug_net(op="DISCONNECTED", start_time=start)

            except Exception as e:
                log_error_infra(service="HTTP", op="DISCONNECT", exc=e)

            finally:
                self.client = self.so_session = None

        await shield(_do_disconnect())
