import asyncio
from collections import OrderedDict
from time import perf_counter
from typing import Any

import acsylla

from src.core.env_conf import ScyllaSettings
from src.core.exceptions import ScyllaNotReachableError


def _scylla_log(msg: acsylla.LogMessage) -> None:
    if str(msg.log_level).lower() in ("error", "crit"):
        print(f"[SCYLLA] {msg.message}", flush=True)


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

        t0 = perf_counter()
        try:
            self._cluster = acsylla.create_cluster(
                self._cfg.scylla_hosts,
                port=self._cfg.scylla_port,
                core_connections_per_host=self._cfg.core_connections_per_host,
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

            if not await self.ping():
                raise ConnectionError("ping failed after session creation")

            self._ready = True
            print(
                f"[SCYLLA] connected host={self._cfg.scylla_hosts} "
                f"keyspace={self._cfg.scylla_keyspace} "
                f"elapsed={1000 * (perf_counter() - t0):.1f}ms",
                flush=True,
            )

        except Exception as e:
            await self._teardown()
            raise ScyllaNotReachableError from e

    async def ping(self) -> bool:
        if self._session is None:
            return False
        try:
            await self._session.execute(
                acsylla.create_statement("SELECT cluster_name FROM system.local")
            )
            return True
        except Exception:
            return False

    async def disconnect(self) -> None:
        if not self._ready:
            return

        t0 = perf_counter()
        try:
            await self._teardown()
            print(
                f"[SCYLLA] disconnected elapsed={1000 * (perf_counter() - t0):.1f}ms",
                flush=True,
            )
        except Exception as e:
            print(f"[SCYLLA] disconnect error: {e}", flush=True)

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

    @staticmethod
    def _bind(
        stmt: acsylla.Statement, params: dict[str, Any] | list[Any] | None = None
    ) -> None:
        if params is None:
            return
        if isinstance(params, dict):
            stmt.bind_dict(params)
        else:
            stmt.bind_list(params)

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
        self._bind(stmt, params)
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
        self._bind(stmt, params)
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
        self._bind(stmt, params)

        if page_state is not None:
            stmt.set_page_state(page_state)

        result = await session.execute(stmt)
        rows = [row.as_tuple() for row in result]
        next_state = result.page_state() if result.has_more_pages() else None
        return rows, next_state

    def is_ready(self) -> bool:
        return self._ready
