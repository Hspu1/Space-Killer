from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .mixins import TimestampMixin, UUIDv7Mixin

if TYPE_CHECKING:
    from .profiles import ProfilesModel
    from .subscriptions import SubscriptionsModel
    from .user_identities import UserIdentitiesModel


class UsersModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "users"

    ####################################################################################

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    ####################################################################################

    identities: Mapped[list["UserIdentitiesModel"]] = relationship(
        "UserIdentitiesModel",
        back_populates="user",
        cascade="save-update, merge",
    )
    profile: Mapped["ProfilesModel"] = relationship(
        "ProfilesModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["SubscriptionsModel"]] = relationship(
        "SubscriptionsModel",
        back_populates="subscriber",
        foreign_keys="[SubscriptionsModel.subscriber_id]",
        cascade="all, delete-orphan",
    )
    subscribers: Mapped[list["SubscriptionsModel"]] = relationship(
        "SubscriptionsModel",
        back_populates="author",
        foreign_keys="[SubscriptionsModel.author_id]",
        cascade="all, delete-orphan",
    )

    ####################################################################################

    __table_args__ = (
        Index(
            "uq_active_users_email",
            "email",
            unique=True,
            postgresql_where=is_active.is_(True),
        ),
    )
