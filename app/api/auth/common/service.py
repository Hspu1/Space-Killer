from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from .schemas import AuthProvider
from app.infra.postgres.database import async_session_maker
from app.infra.postgres.models import UsersModel, UserIdentitiesModel


async def get_user_id(user_info: dict, provider: AuthProvider, provider_user_id: str) -> str:
    async with async_session_maker.begin() as session:
        verify_email = datetime.now(timezone.utc) \
            if user_info.get("email_verified") else None

        stmt = insert(UsersModel).values(
            email=user_info["email"],
            name=user_info.get("name"),
            email_verification_at=verify_email
        )
        user_upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['email'],
            set_={'name': stmt.excluded.name},
            where=(
                    (user_info.get("email_verified")) |
                    (UsersModel.email_verification_at.is_not(None))
            )
        ).returning(UsersModel.id)
        user_id = (await session.execute(user_upsert_stmt)).scalar_one()

        identity_upsert_stmt = (
            insert(UserIdentitiesModel).values(
                user_id=user_id, provider=provider,
                provider_user_id=provider_user_id
            ).on_conflict_do_nothing()
        )

        await session.execute(identity_upsert_stmt)
        return str(user_id)
