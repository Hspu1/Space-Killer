import orjson
import httpx


from src.core.env_conf import centrifugo_stg

# УБРАТЬ ХАРДКОД, ПАРАМЕТРЫ В МЕНЕДЖЕРЕ, ПРОКИНУТЬ В ФАБРРИКУ ПРИЛОЖЕНИЯ
class CentrifugoManager:
    def __init__(self):
        self._api_url = "http://centrifugo:8000/api"
        self._api_key = centrifugo_stg.centrifugo_http_api_key
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        ###
        # ОБРАБОТКУ ОШИБОК ЖЕСТКУЮ ДЕЛАЙ НИГГА
        ###
        if self._client is not None:
            return

        # !!!!!!!!!!!!!! лимиты, хардкод, бля это отвратительно !!!!!!!!!!!!!!
        self._client = httpx.AsyncClient(
            base_url=self._api_url,
            headers={"X-API-Key": self._api_key, "Content-Type": "application/json"},
            limits=httpx.Limits(max_connections=1000, max_keepalive_connections=200, keepalive_expiry=45.0),
            timeout=httpx.Timeout(5.0, connect=2.0),
            http2=True,
        )
        # !!!!!!!!!!!!!! лимиты, хардкод, бля это отвратительно !!!!!!!!!!!!!!

    async def disconnect(self) -> None:
        ###
        # ОБРАБОТКУ ОШИБОК ЖЕСТКУЮ ДЕЛАЙ НИГГА
        ###
        if self._client is None:
            return
 
        await self._client.aclose()
        self._client = None

    async def batch_publish(self, commands: list[dict]) -> None:
        ###
        # ПОЧЕМУ ЭТО COMMANDS ЧЕ ЗА БРЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕЕД
        ###
        if not commands or self._client is None:
            return

        print(f"IN PUBLISHING to CENTRIFUGO, commands: {commands}", flush=True)
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
   
        except httpx.HTTPError as exc:
            print(f"batch_publish failed, frame dropped: {exc}", flush=True)
