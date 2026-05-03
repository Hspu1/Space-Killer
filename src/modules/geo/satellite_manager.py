import asyncio
from datetime import datetime, UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from skyfield.api import load

from src.infra.nats.core_manager import CoreNATSManager
from src.infra.centrifugo import CentrifugoManager

from .update_tle import do_retry, TLE_GROUPS


class SatelliteManager:
    def __init__(self, nats: CoreNATSManager):
        self.ts = load.timescale()
        # self.nats = nats
        self.centrifugo = centrifugo
        self.hz = hz
        self.interval = 1.0 / hz
        self.satellites: dict[str, BaseSatellite] = {}
        self._ticker_task: asyncio.Task | None = None
        self._streaming_channel = "satellites:streaming"

    async def start(self, scheduler: AsyncIOScheduler):
        scheduler.add_job(
            update_tle, 
            "interval", 
            args=[self], 
            hours=1, 
            next_run_time=datetime.now(UTC),
            replace_existing=True
        )
        asyncio.create_task(self._bulk_ticker())

    def update_or_create(self, name: str, l1: str, l2: str):
        if name not in self.satellites:
            self.satellites[name] = BaseSatellite(name)
        self.satellites[name].set_tle(l1, l2, self.ts)

    async def _bulk_ticker(self):
        try:
            while True:
                start_tick = time.perf_counter()
                batch = [
                    sat.get_current_telemetry() 
                    for sat in self.satellites.values() 
                    if sat.satellite is not None
                ]

                if batch:
                    await self.centrifugo.publish_bulk(self._streaming_channel, batch)
                    # await self.nats.publish("skyfield.satellites.bulk", {"data": batch})

                elapsed = time.perf_counter() - start_tick
                await asyncio.sleep(max(0, self.interval - elapsed))
                
        except asyncio.CancelledError:
            print("[SatMgr] Ticker cancelled", flush=True)
            raise

        except Exception as e:
            print(f"[SatMgr] Ticker error: {e}", flush=True)
            await asyncio.sleep(1)


    async def stop(self):
        if not self._ticker_task:
            return

        self._ticker_task.cancel()
        try:
            await asyncio.wait_for(self._ticker_task, return_exceptions=True, 
                timeout=3.0
            )
        except asyncio.TimeoutError:
            print("[SatMgr] Shutdown timed out, some tasks killed forcefully", flush=True)
        finally:
            self._ticker_task = None
            print("[SatMgr] All tasks stopped", flush=True)



@do_retry
async def update_tle(manager: SatelliteManager) -> None:
    for group in TLE_GROUPS:
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
        try:
            response = await client.get(url=url, headers=headers)
            response.raise_for_status()
            content = response.text.strip().splitlines()

            for i in range(0, len(content) - 2, 3):
                name = content[i].strip()
                l1 = content[i+1].strip()
                l2 = content[i+2].strip()
                manager.update_or_create(name, l1, l2)

            print(f"[TLE] Group {group} processed.", flush=True)

        except Exception as e:
            print(f"[TLE] Error updating group {group}: {e}", flush=True)
