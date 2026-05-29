"""SQLAlchemy models for storefront, live, and backoffice customer support."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.orm import Base


class SupportContact(Base):
    """Normalized contact identity for support conversations."""

    __tablename__ = "d2c_support_contacts"
    __table_args__ = (
        UniqueConstraint("contact_code", name="uq_d2c_support_contact_code"),
        UniqueConstraint("customer_id", name="uq_d2c_support_contact_customer"),
        Index("ix_d2c_support_contact_customer", "customer_id"),
        Index("ix_d2c_support_contact_email", "contact_email"),
        Index("ix_d2c_support_contact_phone", "contact_phone"),
        Index("ix_d2c_support_contact_anon", "anonymous_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    contact_code: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    anonymous_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="storefront",
        server_default="storefront",
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
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

    conversations: Mapped[list[SupportConversation]] = relationship(
        back_populates="contact",
        foreign_keys="SupportConversation.contact_id",
    )


class SupportAgentProfile(Base):
    """Backoffice customer service agent profile."""

    __tablename__ = "d2c_support_agent_profiles"
    __table_args__ = (
        UniqueConstraint("agent_code", name="uq_d2c_support_agent_code"),
        UniqueConstraint("email", name="uq_d2c_support_agent_email"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_d2c_support_agent_status"),
        Index("ix_d2c_support_agent_status", "status"),
        Index("ix_d2c_support_agent_email", "email"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_code: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
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

    assigned_conversations: Mapped[list[SupportConversation]] = relationship(
        back_populates="assigned_agent",
        foreign_keys="SupportConversation.assigned_agent_id",
    )
    presence: Mapped[SupportAgentPresence | None] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
        uselist=False,
        foreign_keys="SupportAgentPresence.agent_id",
    )
    live_sessions: Mapped[list[SupportLiveSession]] = relationship(
        back_populates="assigned_agent",
        foreign_keys="SupportLiveSession.assigned_agent_id",
    )


class SupportConversation(Base):
    """Customer support conversation opened from the storefront."""

    __tablename__ = "d2c_support_conversations"
    __table_args__ = (
        UniqueConstraint("conversation_code", name="uq_d2c_support_conv_code"),
        UniqueConstraint("conversation_token_hash", name="uq_d2c_support_conv_token_hash"),
        CheckConstraint(
            "status IN ('open', 'pending_agent', 'pending_customer', 'closed')",
            name="ck_d2c_support_conv_status",
        ),
        CheckConstraint("source IN ('storefront')", name="ck_d2c_support_conv_source"),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high')", name="ck_d2c_support_conv_priority"
        ),
        Index("ix_d2c_support_conv_customer", "customer_id"),
        Index("ix_d2c_support_conv_contact", "contact_id"),
        Index("ix_d2c_support_conv_agent", "assigned_agent_id"),
        Index("ix_d2c_support_conv_anon", "anonymous_id"),
        Index("ix_d2c_support_conv_status", "status"),
        Index("ix_d2c_support_conv_topic", "topic"),
        Index("ix_d2c_support_conv_order", "related_order_no"),
        Index("ix_d2c_support_conv_created", "created_at"),
        Index("ix_d2c_support_conv_last_msg", "last_message_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_code: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    contact_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_agent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="SET NULL"),
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
        default="pending_agent",
        server_default="pending_agent",
    )
    priority: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="normal",
        server_default="normal",
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="storefront",
        server_default="storefront",
    )
    conversation_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_customer_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_agent_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_system_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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

    contact: Mapped[SupportContact | None] = relationship(
        back_populates="conversations",
        foreign_keys=[contact_id],
    )
    assigned_agent: Mapped[SupportAgentProfile | None] = relationship(
        back_populates="assigned_conversations",
        foreign_keys=[assigned_agent_id],
    )
    messages: Mapped[list[SupportMessage]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list[SupportConversationAssignment]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    events: Mapped[list[SupportConversationEvent]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    live_sessions: Mapped[list[SupportLiveSession]] = relationship(
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
        CheckConstraint(
            "visibility IN ('public', 'internal')",
            name="ck_d2c_support_msg_visibility",
        ),
        CheckConstraint(
            "message_kind IN ('text', 'note')",
            name="ck_d2c_support_msg_kind",
        ),
        Index("ix_d2c_support_msg_conv", "conversation_id"),
        Index("ix_d2c_support_msg_agent", "agent_id"),
        Index("ix_d2c_support_msg_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    message_code: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)
    message_kind: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="text",
        server_default="text",
    )
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
    agent: Mapped[SupportAgentProfile | None] = relationship(foreign_keys=[agent_id])


class SupportConversationAssignment(Base):
    """Assignment history for support conversations."""

    __tablename__ = "d2c_support_conversation_assignments"
    __table_args__ = (
        UniqueConstraint("assignment_code", name="uq_d2c_support_assign_code"),
        CheckConstraint("status IN ('active', 'replaced')", name="ck_d2c_support_assign_status"),
        Index("ix_d2c_support_assign_conv", "conversation_id"),
        Index("ix_d2c_support_assign_agent", "agent_id"),
        Index("ix_d2c_support_assign_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    assignment_code: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_by_agent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    replaced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[SupportConversation] = relationship(back_populates="assignments")
    agent: Mapped[SupportAgentProfile] = relationship(foreign_keys=[agent_id])
    assigned_by_agent: Mapped[SupportAgentProfile | None] = relationship(
        foreign_keys=[assigned_by_agent_id],
    )


class SupportConversationEvent(Base):
    """Audit and state transition events for support conversations."""

    __tablename__ = "d2c_support_conversation_events"
    __table_args__ = (
        UniqueConstraint("event_code", name="uq_d2c_support_event_code"),
        CheckConstraint(
            "actor_type IN ('customer', 'agent', 'system')",
            name="ck_d2c_support_event_actor",
        ),
        Index("ix_d2c_support_event_conv", "conversation_id"),
        Index("ix_d2c_support_event_type", "event_type"),
        Index("ix_d2c_support_event_agent", "actor_agent_id"),
        Index("ix_d2c_support_event_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_code: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_agent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    assignment_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_conversation_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default=text("'{}'::json"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversation: Mapped[SupportConversation] = relationship(back_populates="events")
    actor_agent: Mapped[SupportAgentProfile | None] = relationship(
        foreign_keys=[actor_agent_id],
    )
    message: Mapped[SupportMessage | None] = relationship(foreign_keys=[message_id])
    assignment: Mapped[SupportConversationAssignment | None] = relationship(
        foreign_keys=[assignment_id],
    )


class SupportLiveSession(Base):
    """Live chat session opened from the storefront floating widget."""

    __tablename__ = "d2c_support_live_sessions"
    __table_args__ = (
        UniqueConstraint("session_code", name="uq_d2c_supp_live_sess_code"),
        UniqueConstraint("session_token_hash", name="uq_d2c_supp_live_sess_hash"),
        CheckConstraint(
            "status IN ('waiting', 'active', 'ended', 'missed')",
            name="ck_d2c_supp_live_status",
        ),
        CheckConstraint("source IN ('storefront_widget')", name="ck_d2c_supp_live_source"),
        Index("ix_d2c_supp_live_conv", "conversation_id"),
        Index("ix_d2c_supp_live_customer", "customer_id"),
        Index("ix_d2c_supp_live_agent", "assigned_agent_id"),
        Index("ix_d2c_supp_live_anon", "anonymous_id"),
        Index("ix_d2c_supp_live_status", "status"),
        Index("ix_d2c_supp_live_started", "started_at"),
        Index("ix_d2c_supp_live_last_msg", "last_message_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_code: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    anonymous_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    visitor_session_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="waiting",
        server_default="waiting",
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="storefront_widget",
        server_default="storefront_widget",
    )
    session_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_customer_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_agent_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    conversation: Mapped[SupportConversation] = relationship(back_populates="live_sessions")
    assigned_agent: Mapped[SupportAgentProfile | None] = relationship(
        back_populates="live_sessions",
        foreign_keys=[assigned_agent_id],
    )


class SupportAgentPresence(Base):
    """Agent live chat presence state."""

    __tablename__ = "d2c_support_agent_presence"
    __table_args__ = (
        UniqueConstraint("agent_id", name="uq_d2c_supp_pres_agent"),
        UniqueConstraint("agent_code", name="uq_d2c_supp_pres_code"),
        CheckConstraint(
            "presence_status IN ('online', 'away', 'offline')",
            name="ck_d2c_supp_pres_status",
        ),
        CheckConstraint(
            "max_active_sessions >= 1 AND active_session_count >= 0",
            name="ck_d2c_supp_pres_counts",
        ),
        Index("ix_d2c_supp_pres_status", "presence_status"),
        Index("ix_d2c_supp_pres_heartbeat", "last_heartbeat_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_support_agent_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_code: Mapped[str] = mapped_column(String(64), nullable=False)
    presence_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="offline",
        server_default="offline",
    )
    max_active_sessions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )
    active_session_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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

    agent: Mapped[SupportAgentProfile] = relationship(
        back_populates="presence",
        foreign_keys=[agent_id],
    )
