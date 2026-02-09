from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .schemas import AuthProvider
from app.infra import UsersModel, UserIdentitiesModel, async_session_maker


async def get_user_id(user_info: dict, provider: AuthProvider, provider_user_id: str) -> str:
    async with async_session_maker.begin() as session:
        stmt = (
            select(UserIdentitiesModel.user_id)
            .where(
                UserIdentitiesModel.provider == provider,
                UserIdentitiesModel.provider_user_id == provider_user_id
            )
        )
        if user_id := (await session.execute(stmt)).scalar():
            return str(user_id)

        email_verification = datetime.now(timezone.utc) \
            if user_info.get("email_verified") else None

        try:
            async with session.begin_nested():
                user = UsersModel(
                    email=user_info["email"],  full_name=user_info.get("name"),
                    email_verification_at=email_verification
                )
                session.add(user)
                await session.flush()

        except IntegrityError:
            raise Exception("I am gay")

        new_identity = UserIdentitiesModel(
            user_id=user.id, provider=provider,
            provider_user_id=provider_user_id
        )

        session.add(new_identity)
        return str(user.id)
