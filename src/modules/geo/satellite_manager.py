import time
import asyncio
from datetime import datetime, UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from skyfield.api import load
from skyfield.timelib import Timescale

from src.infra.centrifugo import CentrifugoManager
from src.core.env_conf import centrifugo_stg

from .update_tle import do_retry, TLE_GROUPS, client, headers
from .local_tles import TLES
from .base_satellite import BaseSatellite


class SatelliteManager:
    def __init__(self, centrifugo: CentrifugoManager) -> None:
        self.ts: Timescale = load.timescale()
        self.centrifugo = centrifugo
        self.hz = centrifugo_stg.centrifugo_hz
        self.interval = 1.0 / self.hz
        self.satellites: dict[str, BaseSatellite] = {}
        self._ticker_task: asyncio.Task | None = None

    async def start(self, scheduler: AsyncIOScheduler) -> None:
        scheduler.add_job(
            update_tle,
            "interval",
            args=[self],
            hours=1,
            next_run_time=datetime.now(UTC),
            replace_existing=True,
        )
        self._ticker_task = asyncio.create_task(
            self._bulk_ticker(), name="satellite-bulk-ticker"
        )

    def update_or_create(self, name: str, l1: str, l2: str) -> None:
        if name not in self.satellites:
            self.satellites[name] = BaseSatellite(name=name, ts=self.ts)
        self.satellites[name].set_tle(l1=l1, l2=l2, norad_id=int(l1[2:7].strip()))

    async def _bulk_ticker(self) -> None:
        print("starting ticker", flush=True)
        while True:
            start_tick = time.perf_counter()
            current_now_dt = datetime.now(UTC)
            commands = []
            try:
                for sat in self.satellites.values():
                    telemetry = sat.get_current_telemetry(now_dt=current_now_dt)
                    if telemetry is not None:
                        commands.append({
                            "publish": {
                                "channel": f"satellite:{telemetry["id"]}",
                                "data": telemetry,
                                "history_size": 100,
                                "history_ttl": "24h",
                            }
                        })
                    else:
                        print("telemetry is None", flush=True)

                if commands:
                    await self.centrifugo.batch_publish(commands)
            except Exception as e:
                print(e, flush=True)

            print(f"SUCCESS PUBLISHED: {len(commands)} commands", flush=True) 
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
        
        except Exception as e:
            print(f"Unexpected error canceling ticker task: {e}", flush=True)

        finally:
            self._ticker_task = None


@do_retry
async def update_tle(manager: SatelliteManager) -> None:
    for group in TLE_GROUPS:
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
        try:
            response = await client.get(url=url, headers=headers)
            response.raise_for_status()
            # response = TLES  # avoid CelesTrak rate limits
            # content = response.strip().splitlines()
            content = response.text.strip().splitlines()

            for i in range(0, len(content) - 2, 3):
                name = content[i].strip()
                l1 = content[i+1].strip()
                l2 = content[i+2].strip()
                manager.update_or_create(name, l1, l2)

            print(f"[TLE] Group {group} processed.", flush=True)

        except Exception as e:
            print(f"[TLE] Error updating group {group}: {e}", flush=True)
