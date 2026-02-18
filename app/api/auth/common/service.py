from time import perf_counter
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import case, select

from app.api.auth.common.schemas import AuthProvider
from app.infra.postgres.service import PostgresService
from app.infra.postgres.models import UsersModel, UserIdentitiesModel
from app.utils import log_debug_db


async def get_user_id(
        pg_svc: PostgresService, user_info: dict, provider: AuthProvider
) -> str:
    start_select = perf_counter()
    session_maker = pg_svc.get_session_maker()
    async with session_maker() as session:
        stmt = (
            select(UserIdentitiesModel.user_id)
            .where(
                UserIdentitiesModel.provider == provider,
                UserIdentitiesModel.provider_user_id == user_info["id"]
            )
        )

        res = await session.execute(stmt)
        if user_id := res.scalar():
            log_debug_db(
                op="READ", start_time=start_select,
                detail=f"id={str(user_id)[:8]}.."
            )
            return str(user_id)

    start_insert = perf_counter()
    async with session.begin():
        verify_email = datetime.now(timezone.utc) \
            if user_info["email_verified"] else None

        stmt = insert(UsersModel).values(
            email=user_info["email"], name=user_info["name"],
            email_verification_at=verify_email
        )
        user_upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["email"],
            set_={
                "name": stmt.excluded.name,
                "email_verification_at": case(
                    (user_info.get("email_verified") is True,
                     stmt.excluded.email_verification_at),
                    else_=UsersModel.email_verification_at
                )
            }
        ).returning(UsersModel.id)

        user_id = (await session.execute(user_upsert_stmt)).scalar_one()
        identity_upsert_stmt = (
            insert(UserIdentitiesModel).values(
                user_id=user_id, provider=provider,
                provider_user_id=user_info["id"]
            ).on_conflict_do_nothing()
        )
        await session.execute(identity_upsert_stmt)

    log_debug_db(
        op="UPSERT", start_time=start_insert,
        detail=f'email: {user_info["email"]}'
    )
    return str(user_id)
