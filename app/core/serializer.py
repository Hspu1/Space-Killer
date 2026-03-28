from time import perf_counter
from typing import Any, Final

from orjson import (
    OPT_NON_STR_KEYS,
    OPT_SERIALIZE_UUID,
    JSONDecodeError,
    JSONEncodeError,
    dumps,
    loads,
)
from starsessions.serializers import Serializer

from app.utils.log_helpers import log_debug_core, log_error_infra


class OrjsonSerializer(Serializer):
    def __init__(self) -> None:
        self._dump_opts: Final = OPT_NON_STR_KEYS | OPT_SERIALIZE_UUID

    def serialize(self, data: dict[str, Any]) -> bytes:
        start = perf_counter()

        try:
            res = dumps(data, option=self._dump_opts)
            log_debug_core(op="SERIALIZE", start_time=start, detail=f"keys={len(data)}")
            return res

        except (JSONEncodeError, TypeError) as e:
            log_error_infra(service="CORE", op="SERIALIZE", exc=e)
            raise

    def deserialize(self, data: bytes) -> Any:
        if not data:
            return {}

        start = perf_counter()
        try:
            res = loads(data)
            log_debug_core(op="DESERIALIZE", start_time=start, detail=f"size={len(data)}")
            return res

        except (JSONDecodeError, TypeError) as e:
            log_error_infra(service="CORE", op="DESERIALIZE", exc=e)
            return {}
