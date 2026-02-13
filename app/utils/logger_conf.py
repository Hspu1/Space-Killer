import logging
import sys


def setup_logging():
    log_format = (
        "[%(asctime)s] %(module)15s:%(lineno)-3d %(levelname)8s "
        "->    %(message)s"
    )

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
