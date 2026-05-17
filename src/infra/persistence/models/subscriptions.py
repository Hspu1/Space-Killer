from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .mixins import TimestampMixin, UUIDv7Mixin

if TYPE_CHECKING:
    from .users import UsersModel


class SubscriptionsModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "subscriptions"

    ####################################################################################

    subscriber_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    ####################################################################################

    subscriber: Mapped["UsersModel"] = relationship(
        "UsersModel",
        back_populates="subscriptions",
        foreign_keys=[subscriber_id],
    )

    author: Mapped["UsersModel"] = relationship(
        "UsersModel",
        back_populates="subscribers",
        foreign_keys=[author_id],
    )

    ####################################################################################

    __table_args__ = (
        UniqueConstraint("subscriber_id", "author_id", name="uq_subscriber_author"),
        Index("idx_subs_subscriber_id", "subscriber_id"),
        Index("idx_subs_author_id", "author_id"),
    )
