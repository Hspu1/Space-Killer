import asyncio
from datetime import datetime, UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.infra.nats.core_manager import CoreNATSManager

from .coords import ISSData, update_tle


class SatelliteManager:
    def __init__(self, nats: CoreNATSManager):
        self.nats = nats
        self.satellites: dict[str, ISSData] = {
            "ISS": ISSData(nats=nats)
        }
        self._tasks: list[asyncio.Task] = []

    async def start(self, scheduler: AsyncIOScheduler):
        if self._tasks:
            return

        print(f"[SatMgr] Starting telemetry for {list(self.satellites.keys())}", flush=True)
        for name, sat in self.satellites.items():
            task = asyncio.create_task(sat.broadcast(), name=f"broadcast_{name}")
            self._tasks.append(task)
            
            scheduler.add_job(
                update_tle, 
                "interval", 
                args=[sat], 
                hours=1, 
                next_run_time=datetime.now(UTC),
                id=f"update_tle_{name}",
                replace_existing=True
            )

    async def stop(self):
        if not self._tasks:
            return

        print("[SatMgr] Stopping all satellite tasks...", flush=True)
        for task in self._tasks:
            task.cancel()
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True), 
                timeout=3.0
            )
        except asyncio.TimeoutError:
            print("[SatMgr] Shutdown timed out, some tasks killed forcefully", flush=True)
        finally:
            self._tasks.clear()
            print("[SatMgr] All tasks stopped", flush=True)
