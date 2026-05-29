from asyncio import gather
from time import perf_counter
from urllib.parse import urlencode

import httpx
import orjson

from src.core.base import StrictSlots
from src.core.env_conf import SeaweedSettings
from src.utils import log_error_infra
from src.utils.log_helpers import log_debug_seaweed


class SeaweedManager(StrictSlots):
    def __init__(self, config: SeaweedSettings) -> None:
        self._master_url = config.seaweed_master_url.rstrip("/")
        self._master_client: httpx.AsyncClient | None = None
        self._volume_client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        if self._master_client is not None:
            return

        start = perf_counter()

        self._master_client = httpx.AsyncClient(
            base_url=self._master_url,
            limits=httpx.Limits(
                max_connections=8,
                max_keepalive_connections=4,
                keepalive_expiry=60.0,
            ),
            timeout=httpx.Timeout(connect=1.0, read=1.5, write=1.5, pool=2.0),
            http2=True,
        )

        self._volume_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=24,
                max_keepalive_connections=12,
                keepalive_expiry=30.0,
            ),
            timeout=httpx.Timeout(connect=2.0, read=5.0, write=10.0, pool=3.0),
            http2=True,
        )
        log_debug_seaweed(op="CONNECTED", start_time=start)

    async def disconnect(self) -> None:
        if self._master_client is None:
            return

        start = perf_counter()
        try:
            await gather(self._master_client.aclose(), self._volume_client.aclose())
        finally:
            self._master_client, self._volume_client = None, None
            log_debug_seaweed(op="DISCONNECTED", start_time=start)

    async def assign_fid(self, count: int = 1) -> dict | None:
        if self._master_client is None:
            return None

        start = perf_counter()
        params = {"count": count} if count > 1 else None
        try:
            resp = await self._master_client.get("/dir/assign", params=params)
            resp.raise_for_status()
            result: dict = orjson.loads(resp.content)
            log_debug_seaweed(
                op="ASSIGN_FID",
                start_time=start,
                detail=f"count={count}, fid={result.get('fid')}",
            )
            return result

        except Exception as e:
            log_error_infra(service="SEAWEED", op="ASSIGN_FID_ERROR", exc=e)
        return None

    async def upload_blob(
        self,
        volume_url: str,
        fid: str,
        content: bytes,
        filename: str,
        mime_type: str | None = None,
    ) -> dict | None:

        if not (volume_url and fid and content) or self._volume_client is None:
            return None

        start = perf_counter()
        url = f"{_normalize_scheme(volume_url)}/{fid}"
        files = {"file": (filename, content, mime_type or "application/octet-stream")}

        try:
            resp = await self._volume_client.post(url, files=files)
            resp.raise_for_status()
            result: dict = orjson.loads(resp.content)
            log_debug_seaweed(
                op="UPLOAD_BLOB",
                start_time=start,
                detail=f"fid={fid}, size={result.get('size')}",
            )
            return result
        except Exception as e:
            log_error_infra(service="SEAWEED", op="UPLOAD_BLOB_ERROR", exc=e)
        return None

    @staticmethod
    def build_read_url(
        public_url: str,
        fid: str,
        filename: str | None = None,
        resize: dict | None = None,
    ) -> str:

        base = _normalize_scheme(public_url)
        url = f"{base}/{fid}"
        if filename and "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()
            url = f"{url}.{ext}"

        if resize:
            url = f"{url}?{urlencode(resize)}"

        return url

    async def delete_blob(self, volume_url: str, fid: str) -> bool:
        if not (volume_url and fid) or self._volume_client is None:
            return False

        start = perf_counter()
        url = f"{_normalize_scheme(volume_url)}/{fid}"

        try:
            resp = await self._volume_client.delete(url)
            if resp.status_code == 404:
                return True

            resp.raise_for_status()
            log_debug_seaweed(
                op="DELETE_BLOB",
                start_time=start,
                detail=f"fid={fid}",
            )
            return True

        except Exception as e:
            log_error_infra(service="SEAWEED", op="DELETE_BLOB_ERROR", exc=e)
        return False


def _normalize_scheme(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    return f"http://{url}"
