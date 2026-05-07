import asyncio
from datetime import UTC, datetime

from skyfield.api import EarthSatellite, load
from skyfield.timelib import Timescale


class BaseSatellite:
    def __init__(self, name: str):
        self.name = name
        self.norad_id = None 
        self.l1, self.l2 = None, None
        self.satellite = None
        self.is_ready = asyncio.Event()

    def set_tle(self, l1: str, l2: str, norad_id: int, ts):
        self.l1, self.l2 = l1, l2
        new_satellite = EarthSatellite(l1, l2, self.name, ts)
        self.satellite = new_satellite
        self.norad_id = norad_id
        self.is_ready.set()


    def get_current_telemetry(self, now_dt, ts):
        if self.satellite is None:
            return

        now = ts.from_datetime(now_dt)
        geocentric = self.satellite.at(now)
        sub = geocentric.subpoint()
        vel = geocentric.velocity.km_per_s
        speed = (vel @ vel) ** 0.5
        data_epoch = self.satellite.epoch.utc_strftime("%Y-%m-%d %H:%M")

        return {
            "id": self.norad_id,
            "lat": round(sub.latitude.degrees, 6),
            "lng": round(sub.longitude.degrees, 6),
            "alt": round(sub.elevation.km, 3),
            "lst": vel.tolist(),
            "ts": now_dt.timestamp(),
            "v": round(speed, 2), 
            "ep": data_epoch,
        }
