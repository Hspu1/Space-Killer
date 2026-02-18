import logging
from time import perf_counter

from .logger_conf import Colors

logger = logging.getLogger(__name__)


def log_debug_auth(label: str, start: float, provider: str) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start) * 1000
        logger.debug(
            "%s[AUTH] %s%s %s=%s%.2fms%s",
            Colors.PURPLE, provider, Colors.RESET, label,
            Colors.YELLOW, dur, Colors.RESET
        )


def log_error_auth(provider: str, message: str, exc: Exception = None) -> None:
    if exc:
        logger.error(
            "%s[AUTH ERROR] %s%s %s: %s",
            Colors.RED, provider, Colors.RESET, message, exc, exc_info=True
        )
    else:
        logger.error(
            "%s[AUTH ERROR] %s%s %s",
            Colors.RED, provider, Colors.RESET, message
        )


def log_warn_auth(provider: str, message: str, **kwargs) -> None:
    extra = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.warning(
        "%s[AUTH WARN]%s %s%s%s %s %s%s%s",
        Colors.ORANGE, Colors.RESET,
        Colors.LIGHT_GRAY, provider, Colors.RESET, message,
        Colors.YELLOW, extra, Colors.RESET
    )


def log_debug_db(op: str, start_time: float, detail: str = ""):
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[DB]%s %-10s %s%.2fms%s%s",
            Colors.DEEP_BLUE, Colors.RESET, op,
            Colors.YELLOW, dur, Colors.RESET, info
        )


def log_error_infra(service: str, op: str, exc: Exception):
    logger.error(
        "%s[INFRA ERROR]%s %s %s: %s",
        Colors.RED, Colors.RESET, service, op, exc, exc_info=True
    )


def log_debug_core(op: str, start_time: float, detail: str = ""):
    if logger.isEnabledFor(logging.DEBUG):
        dur_us = (perf_counter() - start_time) * 1_000_000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[CORE]%s %-12s %s%.2fµs%s%s",
            Colors.DARK_GREEN, Colors.RESET, op,
            Colors.YELLOW, dur_us, Colors.RESET, info
        )


def log_debug_redis(op: str, start_time: float, detail: str = ""):
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[REDIS]%s %-10s %s%.2fms%s%s",
            Colors.PINK, Colors.RESET, op,
            Colors.YELLOW, dur, Colors.RESET, info
        )


def log_debug_net(op: str, start_time: float, detail: str = ""):
    if logger.isEnabledFor(logging.DEBUG):
        dur = (perf_counter() - start_time) * 1000
        info = f" {Colors.LIGHT_GRAY}({detail}){Colors.RESET}" if detail else ""

        logger.debug(
            "%s[NET]%s %-12s %s%.2fms%s%s",
            Colors.LIGHT_BLUE, Colors.RESET, op,
            Colors.YELLOW, dur, Colors.RESET, info
        )
