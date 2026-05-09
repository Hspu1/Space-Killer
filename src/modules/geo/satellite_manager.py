import time
import asyncio
from datetime import datetime, UTC

import numpy as np
from sgp4.api import SatrecArray
from skyfield.api import load
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.infra.centrifugo import CentrifugoManager
from src.core.env_conf import centrifugo_stg

from .update_tle import do_retry, TLE_GROUPS, client, headers
from .local_tles import TLES
from .base_satellite import BaseSatellite


WGS84_A = 6378.1366
WGS84_B = 6356.7519
E2 = (WGS84_A**2 - WGS84_B**2) / WGS84_A**2
EP2 = (WGS84_A**2 - WGS84_B**2) / WGS84_B**2


class SatelliteManager:
    def __init__(self, centrifugo: CentrifugoManager) -> None:
        self.centrifugo = centrifugo
        self.ts = load.timescale()
        self.satellites: dict[int, BaseSatellite] = {}
        
        self._satrec_array = None
        self._id_map = np.array([], dtype=int)
        self._needs_rebuild = False
        
        self.hz = centrifugo_stg.centrifugo_hz
        self.interval = 1.0 / self.hz

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
        print("Satellite system started: TLE job scheduled, ticker task initiated.")

    async def stop(self) -> None:
        if self._ticker_task:
            self._ticker_task.cancel()
            try:
                await self._ticker_task
            except asyncio.CancelledError:
                pass

    def update_or_create(self, name: str, l1: str, l2: str) -> None:
        try:
            norad_id = int(l1[2:7].strip())
            if norad_id not in self.satellites:
                self.satellites[norad_id] = BaseSatellite(name=name)
            
            if self.satellites[norad_id].set_tle(l1, l2):
                self._needs_rebuild = True
        except Exception as e:
            print(f"Error parsing TLE for {name}: {e}")

    def _rebuild_matrix(self):
        ready_sats = [s for s in self.satellites.values() if s.satrec]
        if not ready_sats:
            return

        self._satrec_array = SatrecArray([s.satrec for s in ready_sats])
        self._id_map = np.array([s.norad_id for s in ready_sats], dtype=np.int32)
        self._needs_rebuild = False
        print(f"Matrix rebuilt: {len(self._id_map)} objects")

    async def _bulk_ticker(self) -> None:
        try:
            while True:
                start_tick = time.perf_counter()
                
                if self._needs_rebuild:
                    self._rebuild_matrix()

                if self._satrec_array:
                    try:
                        t = self.ts.now() 
                        jd_arr = np.full(len(self._id_map), t.ut1_fraction[0])
                        fr_arr = np.full(len(self._id_map), t.ut1_fraction[1])
                        error, r, v = self._satrec_array.sgp4(jd_arr, fr_arr)
                        r = np.array(r).reshape(-1, 3)
                        v = np.array(v).reshape(-1, 3)
                        print(0, flush=True)

                        theta = t.gast * np.pi / 12.0
                        cos_t, sin_t = np.cos(theta), np.sin(theta)
                        rot_matrix = np.array([
                            [cos_t, sin_t, 0],
                            [-sin_t, cos_t, 0],
                            [0, 0, 1]
                        ])
                        print(1, flush=True)

                        x = r[:, 0] * cos_t + r[:, 1] * sin_t
                        y = -r[:, 0] * sin_t + r[:, 1] * cos_t
                        z = r[:, 2]
                        p = np.hypot(x, y)
                        print(2, flush=True)

                        theta_b = np.arctan2(z * WGS84_A, p * WGS84_B)
                        sin_tb, cos_tb = np.sin(theta_b), np.cos(theta_b)
                        lat_rad = np.arctan2(z + EP2 * WGS84_B * (sin_tb**3), p - E2 * WGS84_A * (cos_tb**3))
                        lng_rad = np.arctan2(y, x)
                        print(3, flush=True)

                        sin_lat = np.sin(lat_rad)
                        n_rad = WGS84_A / np.sqrt(1 - E2 * (sin_lat**2))
                        alt_km = (p / np.cos(lat_rad)) - n_rad
                        print(4, flush=True)

                        speed = np.linalg.norm(v, axis=1)
                        combined = np.column_stack((
                            self._id_map,
                            np.degrees(lat_rad),
                            np.degrees(lng_rad),
                            alt_km,
                            speed
                        ))
                        print(5, flush=True)

                        payload = combined.flatten().tolist()
                        commands = ({
                            "publish": {
                                "channel": "satellites:all",
                                "data": {
                                    "v": payload,
                                    "ts": datetime.now(UTC).timestamp()
                                }
                            }
                        }, )
                        await self.centrifugo.batch_publish(commands)

                    except Exception as e:
                        print(f"local fuck: {e}", flush=True)

                elapsed = time.perf_counter() - start_tick
                await asyncio.sleep(max(0.0, self.interval - elapsed))

        except Exception as e:
            print(f"fuck: {e}", flush=True)


@do_retry
async def update_tle(manager: SatelliteManager) -> None:
    for group in TLE_GROUPS:
        url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
        
        try:
            # url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
            # url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
            # response = await client.get(url=url, headers=headers)
            # response.raise_for_status()
            # content = response.text.strip().splitlines()
            # response = TLES  # avoid CelesTrak rate limits
            response = """
                ISS (ZARYA)             
                1 25544U 98067A   26128.19937109  .00004920  00000+0  96926-4 0  9998
                2 25544  51.6308 138.0417 0007476  35.9089 324.2400 15.49139257565554
            """
            content = response.strip().splitlines()

            for i in range(0, len(content) - 2, 3):
                name = content[i].strip()
                l1 = content[i+1].strip()
                l2 = content[i+2].strip()
                manager.update_or_create(name, l1, l2)

            print(f"[TLE] Group {group} processed.", flush=True)

        except Exception as e:
            print(f"[TLE] Error updating group {group}: {e}, {repr(e)}", flush=True)
