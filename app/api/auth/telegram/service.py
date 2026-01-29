import hmac
import hashlib

from fastapi import Request
from fastapi.responses import RedirectResponse

from ..common import get_user_id, AuthProvider
from app.core.env_conf import stg


async def telegram_callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        if data := dict(request.query_params):
            received_hash = data.pop('hash', None)
            data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
            secret_key = hashlib.sha256(stg.telegram_bot_token.encode()).digest()
            expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(expected_hash, received_hash):
                return RedirectResponse(url="/?msg=access_denied")

            user_info_id = str(data["id"])
            user_info = {
                "name": data.get('first_name', 'tg_user'),
                "login": data.get('username', 'tg_user'),
                "email": f"{user_info_id}@telegram.user",
            }

            request.session.clear()
            user_id = await get_user_id(
                user_info=user_info,
                provider=AuthProvider.TELEGRAM,
                provider_user_id=user_info_id
            )
            request.session['user_id'] = user_id
            request.session['given_name'] = user_info['name'] or user_info['login']

            return RedirectResponse(url='/welcome')

    except Exception as e:
        print(f"Telegram Auth Error: {e}")
        return RedirectResponse(url="/?msg=session_expired")
