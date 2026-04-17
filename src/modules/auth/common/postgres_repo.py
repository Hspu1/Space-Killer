from datetime import UTC, datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.infra.persistence.models.users_and_identities import (
    UserIdentitiesModel,
    UsersModel,
)
from src.infra.persistence.postgres import PostgresManager
from src.utils import log_debug_db

from .mappers import AuthProvider, SafeUserInfo


async def pg_resolve_user_id(
    pg_manager: PostgresManager, user_info: SafeUserInfo, provider: AuthProvider
) -> str:
    start_time = perf_counter()
    provider_name, session_maker = provider.value.lower(), pg_manager.get_session_maker()
    async with session_maker.begin() as session:
        stmt = (
            select(UserIdentitiesModel.user_id)
            .join(UsersModel, UserIdentitiesModel.user_id == UsersModel.id)
            .where(
                UserIdentitiesModel.provider == provider_name,
                UserIdentitiesModel.provider_user_id == user_info.id,
                UsersModel.is_active.is_(True),
            )
        )
        if user_id := (await session.execute(stmt)).scalar_one_or_none():
            log_debug_db(op="READ", start_time=start_time, detail=f"id={user_id.hex[:8]}")
            return str(user_id)

        verify_at = datetime.now(UTC) if user_info.email_verified else None
        user_id = (
            await session.execute(
                insert(UsersModel)
                .values(
                    email=user_info.email,
                    name=user_info.name,
                    email_verification_at=verify_at,
                )
                .on_conflict_do_update(
                    index_elements=[UsersModel.email],
                    index_where=(UsersModel.is_active.is_(True)),
                    set_={
                        UsersModel.updated_at: datetime.now(UTC)
                    },  # ensure ID return on conflict
                )
                .returning(UsersModel.id)
            )
        ).scalar_one()

        await session.execute(
            insert(UserIdentitiesModel)
            .values(
                user_id=user_id,
                provider=provider_name,
                provider_user_id=user_info.id,
            )
            .on_conflict_do_nothing(index_elements=["provider", "provider_user_id"])
        )

        log_debug_db(
            op="UPSERT", start_time=start_time, detail=f"email: {user_info.email}"
        )
        return str(user_id)
