from time import perf_counter

import httpx
import orjson

from src.core.env_conf import CentrifugoSettings
from src.utils import log_error_infra
from src.utils.log_helpers import log_debug_centrifugo


class CentrifugoManager:
    def __init__(self, config: CentrifugoSettings) -> None:
        self._api_key = config.centrifugo_http_api_key
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return

        start = perf_counter()
        self._client = httpx.AsyncClient(
            base_url="http://centrifugo:8000/api",
            headers={"X-API-Key": self._api_key, "Content-Type": "application/json"},
            limits=httpx.Limits(
                max_connections=5, max_keepalive_connections=2, keepalive_expiry=60.0
            ),
            timeout=httpx.Timeout(1.0, connect=2.0),  # magic ahh nums
            http2=True,
        )

        log_debug_centrifugo(op="CONNECTED", start_time=start)

    async def disconnect(self) -> None:
        if self._client is None:
            return

        start = perf_counter()
        try:
            await self._client.aclose()
        finally:
            self._client = None
            log_debug_centrifugo(op="DISCONNECTED", start_time=start)

    async def batch_publish(self, commands: tuple[dict]) -> None:
        if not commands or self._client is None:
            return

        payload = orjson.dumps(
            {"commands": commands, "parallel": True},
            option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_UTC_Z,
        )
        try:
            resp = await self._client.post("/batch", content=payload)
            resp.raise_for_status()
            for reply in orjson.loads(resp.content).get("replies", []):
                if error := reply.get("error"):
                    log_error_infra(
                        service="CENTRIFUGO", op=f"BATCH_REPLY_ERROR: {error}"
                    )

        except httpx.HTTPError as e:
            log_error_infra(service="CENTRIFUGO", op=f"BATCH_PUBLISH_ERROR: {e}", exc=e)

        except Exception as e:
            log_error_infra(service="CENTRIFUGO", op=f"UNEXPECTED_ERROR: {e}", exc=e)
