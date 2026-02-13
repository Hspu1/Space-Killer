import logging
import time

from orjson import OPT_NON_STR_KEYS, OPT_SERIALIZE_UUID, dumps, loads, JSONDecodeError, JSONEncodeError
from starsessions.serializers import Serializer

logger = logging.getLogger(__name__)


class OrjsonSerializer(Serializer):
    def __init__(self) -> None:
        self._dump_opts = OPT_NON_STR_KEYS | OPT_SERIALIZE_UUID

    def serialize(self, data: dict) -> bytes:
        start = time.perf_counter()
        try:
            result = dumps(data, option=self._dump_opts)
            logger.info(
                f"[SERIALIZE] total "
                f"\033[93m{(time.perf_counter() - start) * 1_000_000:.4f}µs\033[0m"
            )
            return result
        except (JSONEncodeError, TypeError):
            raise

    def deserialize(self, data: bytes) -> dict:
        if not data:
            return {}
        start = time.perf_counter()
        try:
            result = loads(data)
            logger.info(
                f"[DESERIALIZE] total "
                f"\033[93m{(time.perf_counter() - start) * 1_000_000:.4f}µs\033[0m"
            )
            return result
        except (JSONDecodeError, TypeError):
            raise
