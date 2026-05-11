import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.infra.centrifugo import CentrifugoManager
from src.core.lifespan_helpers import safe_start, silent_close
from src.core.env_conf import centrifugo_stg

from .satellite_manager import SatelliteManager


@asynccontextmanager
async def geo_lifespan():
    centrifugo_manager = CentrifugoManager(config=centrifugo_stg)
    sat_manager = SatelliteManager(centrifugo=centrifugo_manager)
    scheduler = AsyncIOScheduler()

    await safe_start(
        service_name="Centrifugo", coroutine=centrifugo_manager.connect(), atimeout=2.0
    )
    await safe_start(
        service_name="Satellite Manager",
        coroutine=sat_manager.start(scheduler),
        atimeout=1.0,
    )
    scheduler.start()

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await silent_close(service_name="Satellite Manager", coroutine=sat_manager.stop())
        await silent_close(
            service_name="Centrifugo", coroutine=centrifugo_manager.disconnect()
        )


async def main():
    async with geo_lifespan():
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        finally:
            stop_event.set()


if __name__ == "__main__":
    asyncio.run(main())
