import asyncio
from datetime import UTC, datetime

from skyfield.api import EarthSatellite, load
from skyfield.timelib import Timescale


class BaseSatellite:
    def __init__(self, name: str, ts: Timescale):
        self.name = name
        self.l1, self.l2 = None, None
        self.satellite = None
        self.ts = ts
        self.is_ready = asyncio.Event()
        self.subject = f"skyfield.satellites:{self.name.lower()}.coords"

    def set_tle(self, l1: str, l2: str):
        self.l1, self.l2 = l1, l2
        new_satellite = EarthSatellite(l1, l2, self.name, self.ts)
        self.satellite = new_satellite
        self.is_ready.set()


    def get_current_telemetry(self, now_dt):
        if self.satellite is None:
            return
    
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
