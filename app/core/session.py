from orjson import dumps, loads
from starsessions.serializers import Serializer
from itsdangerous import URLSafeSerializer, BadSignature


class OrjsonSerializer(Serializer):
    def __init__(self, key: str):
        self.signer = URLSafeSerializer(key)

    def serialize(self, data: dict) -> bytes:
        return dumps(data)

    def deserialize(self, data: bytes) -> dict:
        return loads(data)

    def encode(self, session_id: str) -> str:
        return self.signer.dumps(session_id)

    def decode(self, signed_id: str) -> str | None:
        try:
            return self.signer.loads(signed_id)

        except BadSignature:
            return None
