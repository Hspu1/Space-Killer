from nats import NATS, connect
from nats.js import JetStreamContext


class NATSManager:
    def __init__(self, config: NATSSettings) -> None:
        self._config = config
        self._client: NATS | None = None
        self._js: JetStreamContext | None = None

    async def connect(self) -> None:
        if self._client and self._client.is_connected:
            return

        try:
            self._client = await connect(
                servers=self._config.nats_servers,
                user=self._config.nats_user,
                password=self._config.nats_password,
                connect_timeout=self._config.nats_connect_timeout,
                reconnect_time_wait=self._config.nats_reconnect_wait,
                max_reconnect_attempts=self._config.nats_max_reconnect,
                ping_interval=self._config.nats_ping_interval,
                max_outstanding_pings=self._config.nats_max_pings,
            )
            
            self._js = self._client.jetstream()
            print("NATS CONNECTED", flush=True)
            await self._setup_infra()

        except Exception as e:
            await self.disconnect()
            raise

    async def _setup_infra(self) -> None:
        if not self._js:
            return
        await self._js.add_stream(name="SKY_DATA", subjects=["skyfield.>"])

    def get_js(self) -> JetStreamContext:
        if not self._js:
            raise RuntimeError("NATS JetStream not initialized")

        return self._js

    async def disconnect(self) -> None:
        if not self._client:
            return

        try:
            await self._client.drain()
            print("NATS DISCONNECTED", flush=True)

        finally:
            self._client, self._js = None, None
