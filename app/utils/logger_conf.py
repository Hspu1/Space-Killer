import logging
import sys
from enum import StrEnum
from typing import Final

IS_TTY: Final = sys.stderr.isatty() or sys.stdout.isatty()


class Colors(StrEnum):
    PURPLE = "\033[35m" if IS_TTY else ""
    CYAN = "\033[36m" if IS_TTY else ""
    YELLOW = "\033[93m" if IS_TTY else ""
    RED = "\033[91m" if IS_TTY else ""
    RESET = "\033[0m" if IS_TTY else ""


FMT: Final = (
    f"{Colors.PURPLE}[%(asctime)s]{Colors.RESET} "
    f"{Colors.CYAN}%(module)15s:%(lineno)-4d{Colors.RESET} "
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
