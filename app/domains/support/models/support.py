"""SQLAlchemy models for storefront customer support conversations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.orm import Base


class SupportConversation(Base):
    """Customer support conversation opened from the storefront."""

    __tablename__ = "d2c_support_conversations"
    __table_args__ = (
        UniqueConstraint("conversation_code", name="uq_d2c_support_conv_code"),
        UniqueConstraint("conversation_token_hash", name="uq_d2c_support_conv_token_hash"),
        CheckConstraint("status IN ('open', 'closed')", name="ck_d2c_support_conv_status"),
        CheckConstraint("source IN ('storefront')", name="ck_d2c_support_conv_source"),
        Index("ix_d2c_support_conv_customer", "customer_id"),
        Index("ix_d2c_support_conv_anon", "anonymous_id"),
        Index("ix_d2c_support_conv_status", "status"),
        Index("ix_d2c_support_conv_topic", "topic"),
        Index("ix_d2c_support_conv_order", "related_order_no"),
        Index("ix_d2c_support_conv_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_code: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    anonymous_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    session_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    related_order_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="open",
        server_default="open",
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="storefront",
        server_default="storefront",
    )
    conversation_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list[SupportMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class SupportMessage(Base):
    """Message in a storefront customer support conversation."""

    __tablename__ = "d2c_support_messages"
    __table_args__ = (
        UniqueConstraint("message_code", name="uq_d2c_support_msg_code"),
        CheckConstraint(
            "sender_type IN ('customer', 'agent', 'system')",
            name="ck_d2c_support_msg_sender",
        ),
        CheckConstraint("visibility IN ('public')", name="ck_d2c_support_msg_visibility"),
        Index("ix_d2c_support_msg_conv", "conversation_id"),
        Index("ix_d2c_support_msg_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_code: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="public",
        server_default=text("'public'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversation: Mapped[SupportConversation] = relationship(back_populates="messages")
