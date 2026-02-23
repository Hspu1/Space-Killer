import hmac
import hashlib
from time import time, perf_counter

from fastapi import Request
from fastapi.responses import RedirectResponse

from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth
from ..common import get_user_id, AuthProvider, get_safe_info
from app.core.env_conf import auth_stg


async def telegram_callback_handling(request: Request, pg_svc: PostgresService) -> RedirectResponse:
    start = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    user_info = dict(request.query_params)
    if not user_info:
        return RedirectResponse(url="/?msg=provider_error")

    received_hash = user_info.pop('hash', None)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(user_info.items()))
    expected_hash = hmac.new(auth_stg.secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not received_hash or not hmac.compare_digest(expected_hash, received_hash):
        return RedirectResponse(url="/?msg=access_denied")
    log_debug_auth(label="crypto_verify", start_time=start, provider=AuthProvider.TELEGRAM)

    try:
        auth_date = int(user_info.get("auth_date", 0))
        if time() - auth_date > auth_stg.tg_session_timeout:
            return RedirectResponse(url="/?msg=session_expired")

        safe_user_info = get_safe_info(user_info=user_info, provider=AuthProvider.TELEGRAM)
        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=safe_user_info,
            provider=AuthProvider.TELEGRAM
        )
        request.session.update(
            {"user_id": user_id, "given_name": safe_user_info['name']}
        )
        log_debug_auth(label="total", start_time=start, provider=AuthProvider.TELEGRAM)
        return RedirectResponse(url='/welcome')

    except Exception as e:
        log_error_auth(provider=AuthProvider.TELEGRAM, message="unexpected", exc=e)
        return RedirectResponse(url="/?msg=provider_error")
