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
                id=f"update_tle_{name}"
            )

    async def stop(self):
        print("[SatMgr] Stopping all satellite tasks...", flush=True)
        for task in self._tasks:
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        print("[SatMgr] All tasks stopped", flush=True)
