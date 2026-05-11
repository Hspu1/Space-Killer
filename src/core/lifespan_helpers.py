from asyncio import wait_for
from collections.abc import Awaitable

from src.core.exceptions import SafeStartError
from src.utils.log_helpers import log_error_infra


async def safe_start(service_name: str, coroutine: Awaitable, atimeout: float) -> None:
    try:
        await wait_for(coroutine, timeout=atimeout)
    except Exception as e:
        log_error_infra(service=service_name, op="STARTUP FAILED", exc=e)
        raise SafeStartError from e


async def silent_close(service_name: str, coroutine: Awaitable) -> None:
    try:
        await wait_for(coroutine, timeout=5.0)
    except Exception as e:
        log_error_infra(service=service_name, op="SHUTDOWN FAILED", exc=e)
