import logging
import time
from typing import Any, Final

from orjson import (
    OPT_NON_STR_KEYS, OPT_SERIALIZE_UUID, dumps, loads,
    JSONDecodeError, JSONEncodeError
)
from starsessions.serializers import Serializer

from app.utils import Colors

logger = logging.getLogger(__name__)


class OrjsonSerializer(Serializer):
    __slots__ = ("_dump_opts",)

    def __init__(self) -> None:
        self._dump_opts: Final = OPT_NON_STR_KEYS | OPT_SERIALIZE_UUID

    def serialize(self, data: dict[str, Any]) -> bytes:
        start = time.perf_counter()

        try:
            res = dumps(data, option=self._dump_opts)
            if logger.isEnabledFor(logging.DEBUG):
                dur = (time.perf_counter() - start) * 1_000_000
                logger.debug(
                    "%s[SERIALIZE]%s total %s%.4fµs%s",
                    Colors.PURPLE, Colors.RESET,
                    Colors.YELLOW, dur, Colors.RESET
                )
            return res

        except (JSONEncodeError, TypeError) as e:
            logger.error(
                "%s[SERIALIZE ERROR]%s -> %s",
                Colors.RED, Colors.RESET, e
            )
            raise

    def deserialize(self, data: bytes) -> dict[str, Any]:
        if not data:
            return {}

        start = time.perf_counter()
        try:
            res = loads(data)
            if logger.isEnabledFor(logging.DEBUG):
                dur = (time.perf_counter() - start) * 1_000_000
                logger.debug(
                    "%s[DESERIALIZE]%s total %s%.4fµs%s",
                    Colors.PURPLE, Colors.RESET,
                    Colors.YELLOW, dur, Colors.RESET
                )
            return res

        except (JSONDecodeError, TypeError) as e:
            logger.error(
                "%s[DESERIALIZE ERROR]%s -> %s",
                Colors.RED, Colors.RESET, e
            )
            return {}
