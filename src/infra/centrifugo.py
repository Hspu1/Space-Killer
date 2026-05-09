import httpx
import orjson

from src.core.env_conf import CentrifugoSettings


class CentrifugoManager:
    def __init__(self, config: CentrifugoSettings) -> None:
        self._api_url = config.centrifugo_api_url
        self._api_key = config.centrifugo_http_api_key
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return

        self._client = httpx.AsyncClient(
            base_url=self._api_url,
            headers={"X-API-Key": self._api_key, "Content-Type": "application/json"},
            limits=httpx.Limits(
                max_connections=5, max_keepalive_connections=2, keepalive_expiry=60.0
            ),
            timeout=httpx.Timeout(1.0, connect=2.0),  # magic ahh nums
            http2=True,
        )

    async def disconnect(self) -> None:
        if self._client is None:
            return

        try:
            await self._client.aclose()
        finally:
            self._client = None

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
                    print(f"batch reply error: {error}", flush=True)

        except httpx.HTTPError as e:
            print(f"batch_publish failed, frame dropped: {e}", flush=True)

        except Exception as e:
            print(f"Unexpected error batch publishing to Centrifugo: {e}", flush=True)
