from orjson import (
    dumps, OPT_NON_STR_KEYS, loads, JSONDecodeError
)
from starsessions.serializers import Serializer


class OrjsonSerializer(Serializer):
    def serialize(self, data: dict) -> bytes:
        return dumps(data, option=OPT_NON_STR_KEYS)

    def deserialize(self, data: bytes) -> dict:
        try:
            return loads(data)
        except (JSONDecodeError, TypeError):
            return {}
