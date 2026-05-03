import os

import orjson
from centrifuge import Client


class CentrifugoManager:
    def __init__(self):
        self._client: Client | None = None

    async def connect(self):
        if self._client and self._client.is_connected():
            return

        self._client = Client(
            address="centrifugo:10000",
            api_key=os.getenv("CENTRIFUGO_HTTP_API_KEY"),
            use_grpc=True,
            grpc_options=[
                ('grpc.max_send_message_length', 10485760),
                ('grpc.max_receive_message_length', 10485760),
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.http2.max_pings_without_data', 0),
            ]
        )

        try:
            await self._client.connect()
            print("CENTRIFUGO gRPC CONNECTED", flush=True)
        except Exception as e:
            print(f"CENTRIFUGO connection error: {e}", flush=True)
            raise

    async def disconnect(self):
        if not self._client:
            return

        try:
            await self._client.disconnect()

        except Exception as e:
            print(f"CENTRIFUGO disconnect error: {e}", flush=True)

        finally:
            print("CENTRIFUGO DISCONNECTED", flush=True)
            self._client = None

    async def publish_bulk(self, channel: str, data):
        if not self._client or not self._client.is_connected():
            print("Centrifugo not connected, skipping publish", flush=True)
            raise RuntimeError("CENTRIFUGO not connected")

        try:
            payload = orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY)
            await self._client.publish(channel, payload)

        except Exception as e:
            print(f"CENTRIFUGO publish error on {channel}: {e}", flush=True)
