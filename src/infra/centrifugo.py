import os

import orjson
from cent import AsyncClient, PublishRequest, CentError


class CentrifugoManager:
    def __init__(self):
        self._client: AsyncClient | None = None

    async def connect(self):
        if self._client:
            return

        self._client = AsyncClient(
            api_url="http://centrifugo:8000/api",
            api_key=os.getenv("CENTRIFUGO_HTTP_API_KEY"),
            timeout=10.0
        )
        print("CENTRIFUGO API READY", flush=True)

    async def disconnect(self):
        if not self._client:
            return
        
        try:
            await self._client.close()
        except Exception as e:
            print(f"CENTRIFUGO close error: {e}", flush=True)
        finally:
            print("CENTRIFUGO API DISCONNECTED", flush=True)
            self._client = None

    async def publish_bulk(self, channel: str, data):
        if not self._client:
            raise RuntimeError("CENTRIFUGO client not initialized")

        try:
            clean_data = orjson.loads(orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY))
            request = PublishRequest(channel=channel, data=clean_data)

            print("publishing to CENTRIFUGO...", flush=True)
            result = await self._client.publish(request)
            # if result.error:
            #     print(f"Centrifugo API error: {result.error.message} ({result.error.code})", flush=True)
                
        except CentError as e:
            print(f"Centrifugo transport/network error: {e}", flush=True)
        except Exception as e:
            print(f"Unexpected error in CentrifugoManager: {e}", flush=True)
