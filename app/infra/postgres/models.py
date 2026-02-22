from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    String, ForeignKey, DateTime,
    Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.postgres.base import Base, TimestampMixin, UUIDv7Mixin


class UsersModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_verification_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, server_default=None)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")  # soft delete
    identities: Mapped[list["UserIdentitiesModel"]] = relationship(
        "UserIdentitiesModel", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_users_name", "name"),)


class UserIdentitiesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "user_identities"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="identities")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
        Index("idx_identities_user_id", "user_id"),
    )
