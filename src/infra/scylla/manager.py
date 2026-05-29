import asyncio
from collections import OrderedDict
from time import perf_counter
from typing import Any

import acsylla

from src.core.env_conf import ScyllaSettings
from src.core.exceptions import ScyllaNotReachableError
from src.utils import log_error_infra
from src.utils.log_helpers import log_debug_scylla


def _scylla_log(msg: acsylla.LogMessage) -> None:
    match msg.log_level.upper():
        case "ERROR" | "CRITICAL":
            log_error_infra(service="SCYLLA", op=f"LOG_ERROR, msg: {msg.message}")
        case _:
            log_debug_scylla(op="CONNECTED", detail=f"LOG: {msg.message}")


class ScyllaManager:
    __slots__ = (
        "_cfg",
        "_cluster",
        "_prep_lock",
        "_prepared",
        "_ready",
        "_session",
    )

    def __init__(self, config: ScyllaSettings) -> None:
        self._cfg = config
        self._cluster: acsylla.Cluster | None = None
        self._session: acsylla.Session | None = None
        self._prepared: OrderedDict[str, acsylla.PreparedStatement] = OrderedDict()
        self._prep_lock = asyncio.Lock()
        self._ready = False

    async def connect(self) -> None:
        if self._ready:
            return

        start = perf_counter()
        try:
            self._cluster = acsylla.create_cluster(
                self._cfg.scylla_hosts,
                port=self._cfg.scylla_port,
                core_connections_per_host=self._cfg.scylla_core_connections_per_host,
                local_port_range_min=self._cfg.scylla_port_range_min,
                local_port_range_max=self._cfg.scylla_port_range_max,
                token_aware_routing=True,
                token_aware_routing_shuffle_replicas=True,
                tcp_nodelay=True,
                connect_timeout=self._cfg.scylla_connect_timeout,
                heartbeat_interval_sec=self._cfg.scylla_heartbeat_interval,
                idle_timeout_sec=self._cfg.scylla_idle_timeout,
                exponential_reconnect_base_delay_ms=self._cfg.scylla_exponential_reconnect_base_delay_ms,
                exponential_reconnect_max_delay_ms=self._cfg.scylla_exponential_reconnect_max_delay_ms,
                application_name=self._cfg.scylla_app_name,
                log_level=self._cfg.scylla_log_level,
                logging_callback=_scylla_log
                if self._cfg.scylla_log_level != "none"
                else None,
                prepare_on_all_hosts=True,
            )

            self._cluster.create_execution_profile(
                "default",
                request_timeout=int(self._cfg.scylla_request_timeout * 1000),
                consistency=acsylla.Consistency.LOCAL_ONE,
                retry_policy="default",
            )

            self._session = await self._cluster.create_session(
                keyspace=self._cfg.scylla_keyspace
            )

            self._ready = True

            log_debug_scylla(
                op="CONNECTED",
                start_time=start,
                detail=f"host={self._cfg.scylla_hosts}, keyspace={
                    self._cfg.scylla_keyspace
                }",
            )

        except Exception as e:
            await self.disconnect()
            raise ScyllaNotReachableError from e

    async def ping(self) -> bool:
        if self._session is None:
            return False

        await self._session.execute(
            acsylla.create_statement("SELECT cluster_name FROM system.local")
        )

    async def disconnect(self) -> None:
        if not self._ready:
            return

        start = perf_counter()
        try:
            await self._teardown()
            log_debug_scylla(op="DISCONNECTED", start_time=start)
        except Exception as e:
            log_error_infra(service="SCYLLA", op="DISCONNECT_ERROR", exc=e)

    async def _teardown(self) -> None:
        try:
            if self._session is not None:
                await self._session.close()
        finally:
            if self._cluster is not None:
                self._cluster.destroy()

            self._prepared.clear()
            self._session, self._cluster, self._ready = None, None, False

    async def _get_prepared(self, query: str) -> acsylla.PreparedStatement:
        if query in self._prepared:
            self._prepared.move_to_end(query)
            return self._prepared[query]

        async with self._prep_lock:
            if query in self._prepared:
                self._prepared.move_to_end(query)
                return self._prepared[query]

            if len(self._prepared) >= self._cfg.scylla_max_prepared:
                self._prepared.popitem(last=False)

            if self._session is None:
                raise ScyllaNotReachableError

            stmt = await self._session.create_prepared(query)
            self._prepared[query] = stmt
            return stmt

    def _assert_ready(self) -> acsylla.Session:
        if not self._ready or self._session is None:
            raise ScyllaNotReachableError
        return self._session

    async def execute(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | None = None,
        profile: str = "default",
    ) -> None:

        session = self._assert_ready()
        prep = await self._get_prepared(query)
        stmt = prep.bind(execution_profile=profile)
        _bind(stmt, params)
        await session.execute(stmt)

    async def fetch_one(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | None = None,
        profile: str = "default",
    ) -> tuple | None:

        session = self._assert_ready()

        prep = await self._get_prepared(query)
        stmt = prep.bind(execution_profile=profile)
        _bind(stmt, params)
        result = await session.execute(stmt)
        return next(iter(result), None)

    async def fetch_page(
        self,
        query: str,
        page_size: int,
        params: dict[str, Any] | list[Any] | None = None,
        page_state: bytes | None = None,
        profile: str = "default",
    ) -> tuple[list[tuple], bytes | None]:

        session = self._assert_ready()
        prep = await self._get_prepared(query)
        stmt = prep.bind(page_size=page_size, execution_profile=profile)
        _bind(stmt, params)

        if page_state is not None:
            stmt.set_page_state(page_state)

        result = await session.execute(stmt)
        rows = [row.as_tuple() for row in result]
        next_state = result.page_state() if result.has_more_pages() else None
        return rows, next_state

    def is_ready(self) -> bool:
        return self._ready


def _bind(
    stmt: acsylla.Statement, params: dict[str, Any] | list[Any] | None = None
) -> None:
    if params is None:
        return

    if isinstance(params, dict):
        stmt.bind_dict(params)
    else:
        stmt.bind_list(params)
