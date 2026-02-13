import logging
import sys


def setup_logging():
    log_format = (
        "\033[35m[%(asctime)s]\033[0m "
        "\033[36m%(module)15s:%(lineno)-4d\033[0m "
        "%(levelname)8s ->    %(message)s"
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("authlib").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
