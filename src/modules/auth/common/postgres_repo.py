from time import perf_counter

from sqlalchemy import case, func, literal, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.expression import Insert, Select

from src.core.exceptions import UserBannedError
from src.infra.persistence.models.models import (
    ProfilesModel,
    UserIdentitiesModel,
    UsersModel,
    UserStatus,
)
from src.infra.persistence.postgres import PostgresManager
from src.utils import log_debug_db

from .mappers import AuthProvider, SafeUserInfo


def _build_fast_way(provider_name: str, provider_user_id: str) -> Select:
    return (
        select(UsersModel.id, UsersModel.status)
        .join(UserIdentitiesModel, UserIdentitiesModel.user_id == UsersModel.id)
        .where(
            UserIdentitiesModel.provider == provider_name,
            UserIdentitiesModel.provider_user_id == provider_user_id,
        )
    )


def _build_upsert_stmt(user_info: SafeUserInfo) -> Insert:
    verify_at = func.now() if user_info.email_verified else None

    safe_status = case(
        (UsersModel.status == UserStatus.BANNED, UsersModel.status),
        else_=literal(UserStatus.ACTIVE, type_=UsersModel.status.type),
    )

    return (
        insert(UsersModel)
        .values(
            email=user_info.email,
            name=user_info.name,
            email_verification_at=verify_at,
            status=UserStatus.ACTIVE,
        )
        .on_conflict_do_update(
            index_elements=[UsersModel.email],
            set_={
                UsersModel.name: user_info.name,
                UsersModel.status: safe_status,
                UsersModel.updated_at: func.now(),
            },
        )
        .returning(UsersModel.id, UsersModel.status)
    )


async def pg_resolve_user_id(
    pg_manager: PostgresManager, user_info: SafeUserInfo, provider: AuthProvider
) -> str:
    start_time = perf_counter()
    provider_name, session_maker = provider.value.lower(), pg_manager.get_session_maker()
    async with session_maker.begin() as session:
        search_stmt = _build_fast_way(
            provider_name=provider_name, provider_user_id=user_info.id
        )
        if res := (await session.execute(search_stmt)).first():
            user_id, status = res.id, res.status

            if status == UserStatus.BANNED:
                raise UserBannedError

            if status == UserStatus.DELETED:
                await session.execute(
                    update(UsersModel)
                    .where(UsersModel.id == user_id)
                    .values(status=UserStatus.ACTIVE, updated_at=func.now())
                )
            log_debug_db(op="READ", start_time=start_time, detail=f"id={user_id.hex[:8]}")
            return str(user_id)

        upsert_stmt = _build_upsert_stmt(user_info=user_info)
        upsert_res = (await session.execute(upsert_stmt)).first()

        user_id, final_status = upsert_res.id, upsert_res.status
        if final_status == UserStatus.BANNED:
            raise UserBannedError

        default_username = f"user-{user_id.hex[-12:]}"
        await session.execute(
            insert(ProfilesModel)
            .values(
                user_id=user_id,
                nickname=user_info.name,
                username=default_username,
            )
            .on_conflict_do_nothing(index_elements=[ProfilesModel.user_id])
        )

        await session.execute(
            insert(UserIdentitiesModel)
            .values(
                user_id=user_id,
                provider=provider_name,
                provider_user_id=user_info.id,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    UserIdentitiesModel.provider,
                    UserIdentitiesModel.provider_user_id,
                ]
            )
        )

        log_debug_db(
            op="UPSERT", start_time=start_time, detail=f"email: {user_info.email}"
        )
        return str(user_id)
