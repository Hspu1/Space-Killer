from time import perf_counter
from typing import Any, Final

from orjson import (
    OPT_NON_STR_KEYS, OPT_SERIALIZE_UUID, dumps, loads,
    JSONDecodeError, JSONEncodeError
)
from starsessions.serializers import Serializer

from app.utils.log_helpers import log_debug_core, log_error_infra


class OrjsonSerializer(Serializer):
    __slots__ = ("_dump_opts",)

    def __init__(self) -> None:
        self._dump_opts: Final = OPT_NON_STR_KEYS | OPT_SERIALIZE_UUID

    def serialize(self, data: dict[str, Any]) -> bytes:
        start = perf_counter()

        try:
            res = dumps(data, option=self._dump_opts)
            log_debug_core(
                op="SERIALIZE", start_time=start,
                detail="keys=%d" % len(data)
            )
            return res

        except (JSONEncodeError, TypeError) as e:
            log_error_infra(service="CORE", op="SERIALIZE", exc=e)
            raise

    def deserialize(self, data: bytes) -> dict[str, Any]:
        if not data:
            return {}

        start = perf_counter()
        try:
            res = loads(data)
            log_debug_core(
                op="DESERIALIZE", start_time=start,
                detail="size=%db" % len(data)
            )
            return res

        except (JSONDecodeError, TypeError) as e:
            log_error_infra(service="CORE", op="DESERIALIZE", exc=e)
            return {}
