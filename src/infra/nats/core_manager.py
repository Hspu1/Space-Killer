import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

import nats
import orjson

from src.core.base import StrictSlots
from src.core.env_conf import NATSSettings
from src.utils import log_error_infra
from src.utils.log_helpers import log_debug_nats


class CoreNATSManager(StrictSlots):
    __slots__ = ("_cfg", "_nc")

    def __init__(self, config: NATSSettings):
        self._cfg = config
        self._nc: nats.NATS | None = None

    async def connect(self):
        if self._nc:
            return

        start = perf_counter()
        self._nc = await nats.connect(
            servers=self._cfg.nats_servers,
            user=self._cfg.nats_user,
            password=self._cfg.nats_password,
            connect_timeout=self._cfg.connect_timeout,
            allow_reconnect=self._cfg.allow_reconnect,
            reconnect_time_wait=self._cfg.reconnect_time_wait,
            max_reconnect_attempts=self._cfg.max_reconnect_attempts,
            ping_interval=self._cfg.ping_interval,
            max_outstanding_pings=self._cfg.max_outstanding_pings,
            error_cb=self.error_cb,
            disconnected_cb=self.disconnected_cb,
            reconnected_cb=self.reconnected_cb,
        )
        log_debug_nats(
            op="CONNECTED",
            start_time=start,
            detail=f"{self._cfg.nats_servers}",
        )

    async def ping(self):
        if not self._nc:
            raise RuntimeError("NATS not reachable")

        try:
            await self._nc.flush(timeout=1.0)

        except TimeoutError:
            raise RuntimeError("NATS ping timeout")
        except Exception as e:
            raise RuntimeError(f"NATS ping failed: {e}")

    async def error_cb(self, e):
        log_error_infra(service="NATS", op=f"ERROR: {e}", exc=e)

    async def disconnected_cb(self):
        log_debug_nats(op="DISCONNECTED (cb)")
        print("NATS Disconnected", flush=True)

    async def reconnected_cb(self):
        log_debug_nats(op="RECONNECTED (cb)")

    async def disconnect(self):
        if not self._nc:
            return

        start = perf_counter()
        try:
            await asyncio.wait_for(self._nc.drain(), timeout=5.0)
        except TimeoutError as e:
            log_error_infra(
                service="NATS",
                op="DRAIN_TIMEOUT",
                exc=e,
            )
            await self._nc.close()
        finally:
            self._nc = None
            log_debug_nats(
                op="DISCONNECTED",
                start_time=start,
            )

    async def publish(self, subject: str, raw: dict[str, Any]):
        if not self._nc:
            raise RuntimeError("NATS not connected")

        try:
            payload = orjson.dumps(raw)
            await self._nc.publish(subject, payload)

        except Exception as e:
            log_error_infra(
                service="NATS",
                op=f"PUBLISH_ERROR on {subject}",
                exc=e,
            )

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
                log_error_infra(
                    service="NATS",
                    op=f"HANDLE_ERROR on {subject}",
                    exc=e,
                )

        return await self._nc.subscribe(
            subject,
            queue=queue,
            cb=_wrapper,
        )
