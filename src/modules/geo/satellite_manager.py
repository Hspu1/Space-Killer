import time
import asyncio
from datetime import datetime, UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from skyfield.api import load

from src.infra.centrifugo import CentrifugoManager

from .update_tle import do_retry, TLE_GROUPS, client
from .local_tles import TLES
from .base_satellite import BaseSatellite


class SatelliteManager:
    def __init__(self, centrifugo: CentrifugoManager):
        self.ts = load.timescale()
        self.centrifugo = centrifugo
        self.hz = 2
        self.interval = 1.0 / self.hz
        self.satellites: dict[str, BaseSatellite] = {}
        self._ticker_task: asyncio.Task | None = None

    async def start(self, scheduler: AsyncIOScheduler) -> None:
        await update_tle(self)  # AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
        scheduler.add_job(
            update_tle,
            "interval",
            args=[self],  # self -> manager
            hours=1,
            next_run_time=datetime.now(UTC),
            replace_existing=True,
        )
        self._ticker_task = asyncio.create_task(
            self._bulk_ticker(), name="satellite-bulk-ticker"
        )

    def update_or_create(self, name: str, l1: str, l2: str) -> None:
        if name not in self.satellites:
            self.satellites[name] = BaseSatellite(name)
        self.satellites[name].set_tle(l1, l2)

    async def _bulk_ticker(self) -> None:
        while True:
            start_tick = time.perf_counter()
            ### ВЕЗДЕ ПРОЖАРЬ AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
            ### ERRORS HANDLINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
            commands = []
            for sat in self.satellites.values():
                try:
                    telemetry = sat.get_current_telemetry()
                    if telemetry is not None:
                        # print(f"SUCCESSFULLY recieved TELEMETRY: {telemetry} for sat: {sat}", flush=True)
                        commands.append({
                            "publish": {
                                "channel": f"satellite:{telemetry["n"].split()[0]}",
                                "data": telemetry,
                                "history_size": 100,
                                "history_ttl": "24h",
                            }
                        })
                    else:
                        pass
                        # print(f"NO TELEMETRY is None: {telemetry} for sat: {sat}", flush=True)
  
                except Exception as e:
                    pass
                    # print(f"FUCKINH BULK TICKER: {e}")

            if commands:
                # print(f"TRYING to PUBLISH to CENTRIFUGO, channel: satellite:{telemetry['n']}", flush=True)
                await self.centrifugo.batch_publish(commands)

            # print(f"SUCCESSFULLY PUBLISHED {len(commands)} commands to CENTRIFUGO", flush=True)
            elapsed = time.perf_counter() - start_tick
            await asyncio.sleep(max(0.0, self.interval - elapsed))

    async def stop(self) -> None:
        if self._ticker_task is None:
            return

        self._ticker_task.cancel()
        try:
            await asyncio.wait_for(self._ticker_task, timeout=3.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        finally:
            self._ticker_task = None
            print("Satellite ticker stopped", flush=True)


@do_retry
async def update_tle(manager: SatelliteManager) -> None:
    for group in TLE_GROUPS:
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
        try:
            # response = await client.get(url=url, headers=headers)
            # response.raise_for_status()
            response = TLES  # avoid CelesTrak rate limits
            # content = response.text.strip().splitlines()
            content = response.strip().splitlines()

            for i in range(0, len(content) - 2, 3):
                name = content[i].strip()
                l1 = content[i+1].strip()
                l2 = content[i+2].strip()
                manager.update_or_create(name, l1, l2)

            print(f"[TLE] Group {group} processed.", flush=True)

        except Exception as e:
            print(f"[TLE] Error updating group {group}: {e}", flush=True)
