import asyncio
from typing import Any, Awaitable, Callable

import nats
import orjson


class CoreNATSManager:
    def __init__(self, config):
        self._config = config
        self._nc: nats.NATS | None = None

    async def connect(self):
        if self._nc:
            return

        self._nc = await nats.connect(
            servers=self._config.nats_servers,
            user=self._config.nats_user,
            password=self._config.nats_password,
            connect_timeout=self._config.connect_timeout,
            allow_reconnect=self._config.allow_reconnect,
            reconnect_time_wait=self._config.reconnect_time_wait,
            max_reconnect_attempts=self._config.max_reconnect_attempts,
            ping_interval=self._config.ping_interval,
            max_outstanding_pings=self._config.max_outstanding_pings,
            error_cb=self.error_cb,
            disconnected_cb=self.disconnected_cb,
            reconnected_cb=self.reconnected_cb,
        )

    async def error_cb(self, e):
        print(f"NATS Error: {e}", flush=True)

    async def disconnected_cb(self):
        print("NATS Disconnected", flush=True)

    async def reconnected_cb(self):
        print(f"NATS Reconnected to {self._nc.connected_url.netloc}", flush=True)

    async def disconnect(self):
        if not self._nc:
            return

        try:
            await asyncio.wait_for(self._nc.drain(), timeout=5.0)
        except asyncio.TimeoutError as e:
            print(f"NATS drain timeout, err: {e}", flush=True)
            await self._nc.close()
        finally:
            print("NATS DISCONNECTED", flush=True)
            self._nc = None

    async def publish(self, subject: str, raw: dict[str, Any]):
        if not self._nc:
            raise RuntimeError("NATS not connected")

        try:
            payload = orjson.dumps(raw)
            await self._nc.publish(subject, payload)

        except Exception as e:
            print(f"NATS publish error on {subject}: {e}", flush=True)

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[bytes], Awaitable[None]],
        queue: str | None = None,
    ):
        if not self._nc:
            raise RuntimeError("NATS not connected")

        async def _wrapper(msg):
            try:
                await handler(msg.data)
            except Exception as e:
                print(f"NATS handler error [{subject}]: {e}", flush=True)

        return await self._nc.subscribe(
            subject,
            queue=queue,
            cb=_wrapper,
        )
