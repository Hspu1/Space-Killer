from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.postgres.base import Base, TimestampMixin, UUIDv7Mixin


class UsersModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    identities: Mapped[list["UserIdentitiesModel"]] = relationship(
        "UserIdentitiesModel",
        back_populates="user",
        cascade="save-update, merge",
    )

    __table_args__ = (
        Index(
            "uq_active_users_email",
            "email",
            unique=True,
            postgresql_where=is_active.is_(True),
        ),
    )


class UserIdentitiesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "user_identities"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="identities")

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_provider_user",
        ),
        Index(
            "idx_identities_user_id",
            "user_id",
        ),
    )
