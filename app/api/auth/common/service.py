from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .schemas import AuthProvider
from app.core import UsersModel, UserIdentitiesModel
from app.core.db.database import async_session_maker


async def get_identity(
        session: AsyncSession,
        provider: AuthProvider, provider_user_id: str
) -> UserIdentitiesModel | None:

    stmt = select(UserIdentitiesModel).where(
        UserIdentitiesModel.provider == provider,
        UserIdentitiesModel.provider_user_id == provider_user_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_email(session: AsyncSession, email: str) -> UsersModel | None:
    stmt = select(UsersModel).where(UsersModel.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_id(user_info: dict, provider: AuthProvider, provider_user_id: str) -> str:
    async with async_session_maker.begin() as session:
        identity = await get_identity(
            session=session, provider=provider,
            provider_user_id=provider_user_id
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
            user_id=user.id, provider=provider,
            provider_user_id=provider_user_id
        )

        session.add(new_identity)
        return str(user.id)
