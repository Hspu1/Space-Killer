from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.auth.google_oauth2.client import google_oauth
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
            session=session, provider="google",
            provider_user_id=user_info["sub"]
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
            user_id=user.id, provider="google",
            provider_user_id=user_info["sub"]
        )
        session.add(new_identity)

        return str(user.id)


async def callback_handling(request: Request) -> RedirectResponse:
    if request.query_params.get("error"):
        return RedirectResponse(url="/?msg=access_denied")

    try:
        token = await google_oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if user_info:
            request.session.clear()
            user_id = await get_user_id(user_info=user_info)
            request.session['user_id'] = user_id
            request.session['given_name'] = user_info.get("given_name", "User")

        return RedirectResponse(url='/welcome')

    except OAuthError:
        return RedirectResponse(url="/?msg=session_expired")
