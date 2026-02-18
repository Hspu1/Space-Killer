import hmac
import hashlib
from time import time, perf_counter

from fastapi import Request
from fastapi.responses import RedirectResponse

from app.infra.postgres.service import PostgresService
from app.utils import log_debug_auth, log_error_auth
from ..common import get_user_id, AuthProvider
from app.core.env_conf import auth_stg


async def telegram_callback_handling(request: Request, pg_svc: PostgresService) -> RedirectResponse:
    start_total = perf_counter()
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    data = dict(request.query_params)
    if not data:
        return RedirectResponse(url="/?msg=provider_error")

    start_crypto = perf_counter()
    received_hash = data.pop('hash', None)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(auth_stg.telegram_bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not received_hash or not hmac.compare_digest(expected_hash, received_hash):
        return RedirectResponse(url="/?msg=access_denied")

    log_debug_auth(label="crypto_verify", start=start_crypto,
                        provider=AuthProvider.TELEGRAM)

    try:
        auth_date = int(data.get("auth_date", 0))
        if time() - auth_date > auth_stg.tg_session_timeout:
            return RedirectResponse(url="/?msg=session_expired")

        user_info_id = str(data.get("id"))
        user_info = {
            "id": user_info_id, "name": data.get('first_name', 'tg_user'),
            "email": f"{user_info_id}@telegram.user", "email_verified": False
        }

        user_id = await get_user_id(
            pg_svc=pg_svc, user_info=user_info,
            provider=AuthProvider.TELEGRAM
        )

        request.session.clear()
        request.session.update(
            {"user_id": user_id, "given_name": user_info['name']}
        )
        log_debug_auth(label="total", start=start_total,
                            provider=AuthProvider.TELEGRAM)
        return RedirectResponse(url='/welcome')

    except Exception as e:
        log_error_auth(provider=AuthProvider.TELEGRAM, message="unexpected", exc=e)
        return RedirectResponse(url="/?msg=provider_error")
