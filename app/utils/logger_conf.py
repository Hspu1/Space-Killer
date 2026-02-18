import logging
import sys
from enum import StrEnum
from typing import Final

IS_TTY: Final = sys.stderr.isatty() or sys.stdout.isatty()


class Colors(StrEnum):
    PURPLE = "\033[38;5;135m" if IS_TTY else ""
    PINK = "\033[38;5;203m" if IS_TTY else ""
    LIGHT_BLUE = "\033[38;5;81m" if IS_TTY else ""
    DEEP_BLUE = "\033[38;5;33m" if IS_TTY else ""
    DARK_GREEN = "\033[38;5;28m" if IS_TTY else ""
    ORANGE = "\033[38;5;208m" if IS_TTY else ""
    YELLOW = "\033[38;5;178m" if IS_TTY else ""
    RED = "\033[38;5;196m" if IS_TTY else ""
    LIGHT_GRAY = "\033[38;5;250m" if IS_TTY else ""
    DARK_GRAY = "\033[38;5;242m" if IS_TTY else ""
    RESET = "\033[0m" if IS_TTY else ""


FMT: Final = (
    f"{Colors.LIGHT_GRAY}[%(asctime)s]{Colors.RESET} "
    f"{Colors.DARK_GRAY}%(module)15s:%(lineno)-4d{Colors.RESET} "
    f"%(levelname)8s ->    %(message)s"
)


def setup_logging(level: int = logging.DEBUG) -> None:
    logging.basicConfig(
        level=level, format=FMT,
        datefmt="%H:%M:%S", force=True
    )

    levels: Final[dict[str, int]] = {
        "asyncio": logging.INFO, "httpx": logging.WARNING,
        "httpcore": logging.WARNING, "authlib": logging.INFO,
        "sqlalchemy.engine": logging.WARNING, "uvicorn.access": logging.INFO
    }

    for name, lvl in levels.items():
        logging.getLogger(name).setLevel(lvl)
