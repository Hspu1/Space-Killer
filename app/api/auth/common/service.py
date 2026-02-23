from time import perf_counter
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from app.api.auth.common.schemas import AuthProvider
from app.infra.postgres.service import PostgresService
from app.infra.postgres.models import UsersModel, UserIdentitiesModel
from app.utils import log_debug_db


async def get_user_id(pg_svc: PostgresService, user_info: dict, provider: AuthProvider) -> str:
    start_time, session_maker = perf_counter(), pg_svc.get_session_maker()
    async with session_maker() as session:
        stmt = select(UserIdentitiesModel.user_id).where(
            UserIdentitiesModel.provider == provider.value.lower(),
            UserIdentitiesModel.provider_user_id == user_info["id"]
        )
        if user_id := (await session.execute(stmt)).scalar():
            log_debug_db(op="READ", start_time=start_time, detail="id=%s..." % str(user_id)[:8])
            return str(user_id)

    async with session_maker.begin() as session:
        verify_at = datetime.now(timezone.utc) if user_info["email_verified"] else None
        user_id = (await session.execute(
            insert(UsersModel).values(
                email=user_info["email"], name=user_info["name"],
                email_verification_at=verify_at).on_conflict_do_update(index_elements=["email"],
                    set_={"name": UsersModel.name}  # dummy update to force RETURNING id
            ).returning(UsersModel.id)
        )).scalar_one()

        await session.execute(
            insert(UserIdentitiesModel).values(
                user_id=user_id, provider=provider.value.lower(),
                provider_user_id=user_info["id"]
            ).on_conflict_do_nothing(index_elements=["provider", "provider_user_id"])
        )

    log_debug_db(op="UPSERT", start_time=start_time, detail="email: %s" % user_info["email"])
    return str(user_id)
