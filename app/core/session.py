from orjson import (
    OPT_NON_STR_KEYS, OPT_SERIALIZE_UUID,
    dumps, loads, JSONDecodeError, JSONEncodeError
)
from starsessions.serializers import Serializer


class OrjsonSerializer(Serializer):
    def __init__(self) -> None:
        self._dump_opts = OPT_NON_STR_KEYS | OPT_SERIALIZE_UUID
        # options = serializing not only str keys | UUID -> str

    def serialize(self, data: dict) -> bytes:
        try:
            return dumps(data, option=self._dump_opts)
            # dict -> bytes (using our options)
        except (JSONEncodeError, TypeError):
            raise

    def deserialize(self, data: bytes) -> dict:
        if not data:
            return {}

        try:
            return loads(data)  # bytes -> dict
        except (JSONDecodeError, TypeError):
            raise
