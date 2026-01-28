import hmac
import hashlib
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.env_conf import stg
from app.core import UsersModel, UserIdentitiesModel
from app.core.db.database import async_session_maker


async def get_identity(
        session: AsyncSession, provider: str, provider_user_id: str
) -> UserIdentitiesModel | None:

    stmt = select(UserIdentitiesModel).where(
        UserIdentitiesModel.provider == provider,
        UserIdentitiesModel.provider_user_id == provider_user_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_email(session: AsyncSession, email: str) -> UsersModel | None:
    stmt = select(UsersModel).where(UsersModel.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_id(user_info: dict) -> str:
    async with async_session_maker.begin() as session:
        identity = await get_identity(
            session=session, provider="telegram",
            provider_user_id=user_info["id"]
        )
        if identity:
            return str(identity.user_id)

        user = await get_email(session=session, email=user_info["email"])
        email_verification = datetime.now(timezone.utc) \
            if user_info.get("email_verified") else None

        if not user:
            try:
                async with session.begin_nested():  # SAVEPOINT
                    user = UsersModel(
                        email=user_info["email"],  full_name=user_info.get("name"),
                        email_verification_at=email_verification
                    )
                    session.add(user)
                    await session.flush()

            except IntegrityError:
                user = await get_email(session=session, email=user_info["email"])

        new_identity = UserIdentitiesModel(
            user_id=user.id, provider="telegram",
            provider_user_id=user_info["id"]
        )
        session.add(new_identity)

        return str(user.id)


async def telegram_callback_handling(request: Request):
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

            user_info = {
                "id": data['id'],
                "name": data.get('first_name', 'tg_user'),
                "login": data.get('username', 'tg_user'),
                "email": f"{data['id']}@telegram.user",
                "email_verified": True
            }

            request.session.clear()
            user_id = await get_user_id(user_info=user_info)
            request.session['user_id'] = user_id
            request.session['given_name'] = user_info['name'] or user_info['login']

            return RedirectResponse(url='/welcome')

    except Exception as e:
        print(f"Telegram Auth Error: {e}")
        return RedirectResponse(url="/?msg=session_expired")
