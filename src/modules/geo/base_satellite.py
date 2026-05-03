import asyncio
from datetime import UTC, datetime

from skyfield.api import EarthSatellite, load

from src.infra.nats.core_manager import CoreNATSManager


class BaseSatellite:
    def __init__(self, name: str, nats: CoreNATSManager = None, interval: float = 0.5):
        self.name = name
        self.nats = nats | None
        self.interval = interval
        self.l1, self.l2 = None, None
        self.satellite = None
        self.ts = load.timescale()
        self.is_ready = asyncio.Event()
        self.subject = f"skyfield.satellites:{self.name.lower()}.coords"

    def set_tle(self, l1: str, l2: str):
        self.l1, self.l2 = l1, l2
        new_satellite = EarthSatellite(l1, l2, self.name, self.ts)
        self.satellite = new_satellite
        self.is_ready.set()


    def get_current_telemetry(self):
        if self.satellite is None:
            return
    
        now_dt = datetime.now(UTC)
        now = self.ts.from_datetime(now_dt)
        geocentric = self.satellite.at(now)
        sub = geocentric.subpoint()
        vel = geocentric.velocity.km_per_s
        speed = (vel @ vel) ** 0.5 * 3600
        data_epoch = self.satellite.epoch.utc_strftime("%Y-%m-%d %H:%M")

        return {
            "n": self.name,
            "lat": sub.latitude.degrees,
            "lng": sub.longitude.degrees,
            "alt": sub.elevation.km,
            "lst": vel.tolist(),
            "v": speed,
            "ts": now_dt.timestamp(),
            "ep": data_epoch,
        }

    # async def broadcast(self):
    #     try:
    #         print(f"[{self.name}] BROADCAST: Waiting for TLE...", flush=True)
    #         await self.is_ready.wait()
    #         print(f"[{self.name}] BROADCAST: Started", flush=True)

    #         while True:
    #             raw = await asyncio.to_thread(self.get_current_telemetry)
    #             await self.nats.publish(self.subject, raw)
    #             await asyncio.sleep(self.interval)

    #     except asyncio.CancelledError:
    #         print(f"[{self.name}] BROADCAST: Cancelled safely", flush=True)
    #         raise

    #     except Exception as e:
    #         print(f"[{self.name}] BROADCAST ERROR: {type(e).__name__}: {e}", flush=True)
    #         await asyncio.sleep(5)
