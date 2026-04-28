import asyncio
from typing import Callable, Awaitable

import orjson
import nats


class CoreNATSManager:
    def __init__(self, config):
        self._config = config
        self._nc: nats.NATS | None = None

    async def connect(self):
        if self._nc and self._nc.is_connected:
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
        )

        print("NATS CONNECTED", flush=True)

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

    async def publish(self, subject: str, payload: bytes):
        if not self._nc or not self._nc.is_connected:
            raise RuntimeError("NATS not connected")

        print("[NATS] publish", subject, payload, flush=True)
        await self._nc.publish(subject, payload)

    async def publish_json(self, subject: str, data: dict):
        await self.publish(subject, orjson.dumps(data))

    async def subscribe(self, subject: str, handler: Callable[[bytes], Awaitable[None]], queue: str | None = None):
        if not self._nc or not self._nc.is_connected:
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
