import asyncio
from datetime import UTC, datetime
from typing import Final

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from httpx import (
    AsyncClient,
    HTTPStatusError,
    Limits,
    RequestError,
)
import orjson
from skyfield.api import EarthSatellite, load
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_500_INTERNAL_SERVER_ERROR
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from src.infra.nats.core_manager import CoreNATSManager
from src.core.env_conf import auth_stg, http_stg, server_stg, nats_stg
from src.utils.log_helpers import log_warn_auth

limits: Final[Limits] = Limits(
    max_connections=http_stg.max_connections,
    max_keepalive_connections=http_stg.max_keepalive_connections,
    keepalive_expiry=http_stg.keepalive_expiry,
)
client: Final[AsyncClient] = AsyncClient(
    # proxy=server_stg.proxy,
    limits=limits,
    timeout=auth_stg.auth_timeout,
    verify=server_stg.ssl_check,
)
headers: Final[dict[str, str]] = {
    "Accept": "text/plain",
    "User-Agent": "Smth-P",
}


def is_retryable(e: Exception) -> bool:
    if isinstance(e, RequestError):
        return True

    if isinstance(e, HTTPStatusError):
        return (
            e.response.status_code >= HTTP_500_INTERNAL_SERVER_ERROR
            or e.response.status_code == HTTP_429_TOO_MANY_REQUESTS
        )
    return False


def log_retry(retry_state: RetryCallState) -> None:
    exc, detail = retry_state.outcome.exception(), "Unknown Error"
    if isinstance(exc, HTTPStatusError):
        status = exc.response.status_code
        try:
            detail = f"Status: {status}, Body: {exc.response.text[:250]}"
        except Exception:
            detail = f"Status: {status} (Body is unreadable)"
    elif exc:
        detail = f"Cannnot get status and body, exc: {exc}"

    log_warn_auth(
        provider="HTTP-PRACTIECE",
        message=f"COORDS attempt {retry_state.attempt_number} failed. Detail: {detail}",
    )


do_retry: Final = retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=5),
    reraise=True,
    before_sleep=log_retry,
)


class ISSData:
    def __init__(self, nats: CoreNATSManager):
        self.nats = nats
        self.l1, self.l2 = None, None
        self.satellite = None
        self.ts = load.timescale()
        self.is_ready = asyncio.Event()

    def set_tle(self, l1, l2):
        self.l1, self.l2 = l1, l2
        new_satellite = EarthSatellite(l1, l2, "ISS", self.ts)
        self.satellite = new_satellite
        self.is_ready.set()

    def get_current_telemetry(self):
        if self.satellite is None:
            raise RuntimeError("Satellite not initialized (TLE missing)")

        now = self.ts.from_datetime(datetime.now(UTC))
        geocentric = self.satellite.at(now)
        sub = geocentric.subpoint()
        vel = geocentric.velocity.km_per_s
        speed = (vel @ vel) ** 0.5 * 3600
        data_epoch = self.satellite.epoch.utc_strftime("%Y-%m-%d %H:%M")

        return {
            "lat": sub.latitude.degrees,
            "lng": sub.longitude.degrees,
            "alt": sub.elevation.km,
            "speed": speed,
            "data_epoch": data_epoch,
        }

    async def broadcast(self):
        try:
            await self.is_ready.wait()
            
            while True:
                raw = self.get_current_telemetry()  # !!! Vectorizarion (and stuff) impl for the future !!!
                await self.nats.publish("skyfield.iss.coords", raw)
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError as e:
            print(f"[ISS] BROADCAST: Task cancelled safely: {e}", flush=True)
            raise

        except Exception as e:
            print(f"[ISS] BROADCAST: CRITICAL ERROR: {type(e).__name__}: {e}", flush=True)
            await asyncio.sleep(5)




@do_retry
async def update_tle(iss_data: ISSData) -> None:
    print(
        f"\n[deprecated TLEs]\n"
        f"L1: {iss_data.l1 or 'no data'}\n"
        f"L2: {iss_data.l2 or 'no data'}"
    )
    response = await client.get(
        url="https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle",
        headers=headers,
    )
    response.raise_for_status()

    if len(lines := response.text.strip().splitlines()) >= 3:  # noqa
        iss_data.set_tle(lines[1], lines[2])
        print(f"\n[new TLEs]\nL1: {iss_data.l1}\nL2: {iss_data.l2}")
