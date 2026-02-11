import time
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import or_, select

from .schemas import AuthProvider
from app.infra.postgres.database import async_session_maker
from app.infra.postgres.models import UsersModel, UserIdentitiesModel


async def get_user_id(user_info: dict, provider: AuthProvider, provider_user_id: str) -> str:
    start_time = time.perf_counter()
    async with async_session_maker.begin() as session:
        stmt = (
            select(UserIdentitiesModel.user_id)
            .where(
                UserIdentitiesModel.provider == provider,
                UserIdentitiesModel.provider_user_id == provider_user_id
            )
        )
        if user_id := (await session.execute(stmt)).scalar():
            print(f"[DB] READ total: {time.perf_counter() - start_time:.4f}s")
            return str(user_id)

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
            where=or_(
                user_info.get("email_verified", False),
                UsersModel.email_verification_at.is_not(None)
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

    print(f"[DB] WRITE/UPDATE total: {(time.perf_counter() - start_time):.4f}s")
    return str(user_id)
