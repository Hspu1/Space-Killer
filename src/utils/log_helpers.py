import logging
from time import perf_counter
from typing import Any

from .logger_conf import Colors

logger = logging.getLogger(__name__)


def log_debug_auth(label: str, start_time: float, provider: str) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000

        logger.debug(
            "%s[AUTH] %s%s %s=%s%.2fms%s",
            Colors.PURPLE,
            provider,
            Colors.RESET,
            label,
            Colors.YELLOW,
            dur,
            Colors.RESET,
        )


def log_error_auth(provider: str, message: str, exc: Exception | None = None) -> None:
    if logger.isEnabledFor(logging.ERROR):
        if exc:
            logger.error(
                "%s[AUTH ERROR] %s%s %s: %s",
                Colors.RED,
                provider,
                Colors.RESET,
                message,
                exc,
                exc_info=isinstance(exc, Exception),
            )

        else:
            logger.error(
                "%s[AUTH ERROR] %s%s %s", Colors.RED, provider, Colors.RESET, message
            )


def log_warn_auth(provider: str, message: str, **kwargs: Any) -> None:
    if logger.isEnabledFor(logging.WARNING):
        extra = " ".join([f"{k}={v}" for k, v in kwargs.items()])

        logger.warning(
            "%s[AUTH WARN]%s %s%s%s %s %s%s%s",
            Colors.ORANGE,
            Colors.RESET,
            Colors.LIGHT_GRAY,
            provider,
            Colors.RESET,
            message,
            Colors.YELLOW,
            extra,
            Colors.RESET,
        )


def log_debug_db(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[DB]%s %s %s%.2fms%s%s",
            Colors.DEEP_BLUE,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_error_infra(
    service: str,
    op: str,
    exc: Exception | str = "",
    exc_tuple: tuple[Any, ...] | str = "",
) -> None:
    if logger.isEnabledFor(logging.ERROR):
        logger.error(
            "%s[INFRA ERROR]%s %s %s: %s %s",
            Colors.RED,
            Colors.RESET,
            service,
            op,
            exc,
            exc_tuple,
            exc_info=isinstance(exc, Exception),
        )


def log_debug_core(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur_us = (perf_counter() - start_time) * 1_000_000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[CORE]%s %s %s%.2fµs%s%s",
            Colors.DARK_GREEN,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur_us,
            Colors.RESET,
            info,
        )


def log_debug_redis(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[REDIS]%s %s %s%.2fms%s%s",
            Colors.PINK,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_nats(op: str, start_time: float = 0.0, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[NATS]%s %s %s%.2fms%s%s",
            Colors.PINK,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_centrifugo(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[CENTRIFUGO]%s %s %s%.2fms%s%s",
            Colors.PINK,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_scylla(op: str, start_time: float | None, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000 if start_time is not None else 0
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[SCYLLA]%s %s %s%.2fms%s%s",
            Colors.PINK,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_seaweed(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[SEAWEED]%s %s %s%.2fms%s%s",
            Colors.PINK,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_http(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[HTTP]%s %s %s%.2fms%s%s",
            Colors.LIGHT_BLUE,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_limiter(op: str, start_time: float, detail: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[REDIS LIMITER]%s %s %s%.2fms%s%s",
            Colors.PINK,
            Colors.RESET,
            op,
            Colors.YELLOW,
            dur,
            Colors.RESET,
            info,
        )


def log_debug_login(start_time: float, provider: str = "") -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000

        logger.debug(
            "%s[AUTH LOGIN]%s %s %s%.2fms%s provider=%s",
            Colors.PURPLE,
            Colors.RESET,
            "",
            Colors.YELLOW,
            dur,
            Colors.RESET,
            provider.upper(),
        )


def log_healthz(success: bool, e: Exception | None = None) -> None:
    if success and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "%s[HEALTHZ]%s STATUS: SUCCESS",
            Colors.DARK_GREEN,
            Colors.RESET,
        )

    if e and logger.isEnabledFor(logging.ERROR):
        if isinstance(e, ExceptionGroup):
            errors_list = [f"{type(err).__name__}: {err}" for err in e.exceptions]
            err_msg = " | ".join(errors_list)
        else:
            err_msg = f"{type(e).__name__}: {e}"

        logger.error(
            "%s[HEALTHZ]%s STATUS: FUCKED | %s",
            Colors.RED,
            Colors.RESET,
            err_msg,
        )
