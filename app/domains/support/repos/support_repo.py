"""Repositories for storefront, live, and backoffice support conversations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from app.domains.support.models.support import (
    SupportAgentPresence,
    SupportAgentProfile,
    SupportContact,
    SupportConversation,
    SupportConversationAssignment,
    SupportConversationEvent,
    SupportLiveSession,
    SupportMessage,
)

SupportConversationWithCount = tuple[SupportConversation, int]


def create_contact(session: Session, contact: SupportContact) -> SupportContact:
    session.add(contact)
    session.flush()
    return contact


def get_contact_by_customer_id(session: Session, customer_id: int) -> SupportContact | None:
    statement = select(SupportContact).where(SupportContact.customer_id == customer_id)
    return session.scalar(statement)


def get_contact_by_email(session: Session, contact_email: str) -> SupportContact | None:
    statement = (
        select(SupportContact)
        .where(SupportContact.contact_email == contact_email)
        .order_by(SupportContact.id)
        .limit(1)
    )
    return session.scalar(statement)


def get_contact_by_phone(session: Session, contact_phone: str) -> SupportContact | None:
    statement = (
        select(SupportContact)
        .where(SupportContact.contact_phone == contact_phone)
        .order_by(SupportContact.id)
        .limit(1)
    )
    return session.scalar(statement)


def create_agent_profile(
    session: Session,
    agent: SupportAgentProfile,
) -> SupportAgentProfile:
    session.add(agent)
    session.flush()
    return agent


def get_agent_by_code(
    session: Session,
    agent_code: str,
) -> SupportAgentProfile | None:
    statement = select(SupportAgentProfile).where(SupportAgentProfile.agent_code == agent_code)
    return session.scalar(statement)


def get_active_agent_by_code(
    session: Session,
    agent_code: str,
) -> SupportAgentProfile | None:
    statement = (
        select(SupportAgentProfile)
        .where(SupportAgentProfile.agent_code == agent_code)
        .where(SupportAgentProfile.status == "active")
    )
    return session.scalar(statement)


def list_agent_profiles(session: Session) -> list[SupportAgentProfile]:
    statement = select(SupportAgentProfile).order_by(
        SupportAgentProfile.status,
        SupportAgentProfile.display_name,
        SupportAgentProfile.id,
    )
    return list(session.scalars(statement).all())


def create_conversation(
    session: Session,
    conversation: SupportConversation,
) -> SupportConversation:
    session.add(conversation)
    session.flush()
    return conversation


def create_message(
    session: Session,
    message: SupportMessage,
) -> SupportMessage:
    session.add(message)
    session.flush()
    return message


def create_assignment(
    session: Session,
    assignment: SupportConversationAssignment,
) -> SupportConversationAssignment:
    session.add(assignment)
    session.flush()
    return assignment


def create_event(
    session: Session,
    event: SupportConversationEvent,
) -> SupportConversationEvent:
    session.add(event)
    session.flush()
    return event


def replace_active_assignments(
    session: Session,
    conversation_id: int,
    replaced_at: datetime,
) -> None:
    session.execute(
        update(SupportConversationAssignment)
        .where(SupportConversationAssignment.conversation_id == conversation_id)
        .where(SupportConversationAssignment.status == "active")
        .values(status="replaced", replaced_at=replaced_at)
    )
    session.flush()


def get_conversation_by_code(
    session: Session,
    conversation_code: str,
) -> SupportConversation | None:
    statement = select(SupportConversation).where(
        SupportConversation.conversation_code == conversation_code
    )
    return session.scalar(statement)


def list_messages_for_conversation(
    session: Session,
    conversation_id: int,
) -> list[SupportMessage]:
    statement = (
        select(SupportMessage)
        .where(SupportMessage.conversation_id == conversation_id)
        .order_by(SupportMessage.created_at, SupportMessage.id)
    )
    return list(session.scalars(statement).all())


def list_events_for_conversation(
    session: Session,
    conversation_id: int,
) -> list[SupportConversationEvent]:
    statement = (
        select(SupportConversationEvent)
        .where(SupportConversationEvent.conversation_id == conversation_id)
        .order_by(SupportConversationEvent.created_at, SupportConversationEvent.id)
    )
    return list(session.scalars(statement).all())


def _conversation_count_statement(
    customer_id: int,
) -> Select[tuple[SupportConversation, int]]:
    return (
        select(
            SupportConversation,
            func.count(SupportMessage.id).label("message_count"),
        )
        .outerjoin(
            SupportMessage,
            SupportMessage.conversation_id == SupportConversation.id,
        )
        .where(SupportConversation.customer_id == customer_id)
        .group_by(SupportConversation.id)
        .order_by(SupportConversation.updated_at.desc(), SupportConversation.id.desc())
    )


def list_conversations_by_customer(
    session: Session,
    customer_id: int,
) -> list[SupportConversationWithCount]:
    rows = session.execute(_conversation_count_statement(customer_id)).all()
    return [(conversation, int(message_count or 0)) for conversation, message_count in rows]


def list_backoffice_conversations(
    session: Session,
    *,
    status_filter: str | None = None,
    topic: str | None = None,
    assigned_agent_id: int | None = None,
) -> list[SupportConversationWithCount]:
    statement = (
        select(
            SupportConversation,
            func.count(SupportMessage.id).label("message_count"),
        )
        .outerjoin(
            SupportMessage,
            SupportMessage.conversation_id == SupportConversation.id,
        )
        .group_by(SupportConversation.id)
        .order_by(
            SupportConversation.last_message_at.desc().nullslast(),
            SupportConversation.created_at.desc(),
            SupportConversation.id.desc(),
        )
    )

    if status_filter is not None:
        statement = statement.where(SupportConversation.status == status_filter)

    if topic is not None:
        statement = statement.where(SupportConversation.topic == topic)

    if assigned_agent_id is not None:
        statement = statement.where(SupportConversation.assigned_agent_id == assigned_agent_id)

    rows = session.execute(statement).all()
    return [(conversation, int(message_count or 0)) for conversation, message_count in rows]


def create_live_session(
    session: Session,
    live_session: SupportLiveSession,
) -> SupportLiveSession:
    session.add(live_session)
    session.flush()
    return live_session


def get_live_session_by_code(
    session: Session,
    session_code: str,
) -> SupportLiveSession | None:
    statement = select(SupportLiveSession).where(SupportLiveSession.session_code == session_code)
    return session.scalar(statement)


def list_live_sessions(
    session: Session,
    *,
    status_filter: str | None = None,
    assigned_agent_id: int | None = None,
) -> list[SupportLiveSession]:
    statement = select(SupportLiveSession).order_by(
        SupportLiveSession.last_message_at.desc().nullslast(),
        SupportLiveSession.started_at.desc(),
        SupportLiveSession.id.desc(),
    )

    if status_filter is not None:
        statement = statement.where(SupportLiveSession.status == status_filter)

    if assigned_agent_id is not None:
        statement = statement.where(SupportLiveSession.assigned_agent_id == assigned_agent_id)

    return list(session.scalars(statement).all())


def count_live_sessions_by_status(session: Session, status_filter: str) -> int:
    statement = select(func.count(SupportLiveSession.id)).where(
        SupportLiveSession.status == status_filter
    )
    return int(session.scalar(statement) or 0)


def count_active_live_sessions_for_agent(session: Session, agent_id: int) -> int:
    statement = (
        select(func.count(SupportLiveSession.id))
        .where(SupportLiveSession.assigned_agent_id == agent_id)
        .where(SupportLiveSession.status == "active")
    )
    return int(session.scalar(statement) or 0)


def create_agent_presence(
    session: Session,
    presence: SupportAgentPresence,
) -> SupportAgentPresence:
    session.add(presence)
    session.flush()
    return presence


def get_agent_presence_by_agent_id(
    session: Session,
    agent_id: int,
) -> SupportAgentPresence | None:
    statement = select(SupportAgentPresence).where(SupportAgentPresence.agent_id == agent_id)
    return session.scalar(statement)


def get_agent_presence_by_agent_code(
    session: Session,
    agent_code: str,
) -> SupportAgentPresence | None:
    statement = select(SupportAgentPresence).where(SupportAgentPresence.agent_code == agent_code)
    return session.scalar(statement)


def list_agent_presence(session: Session) -> list[SupportAgentPresence]:
    statement = select(SupportAgentPresence).order_by(
        SupportAgentPresence.presence_status,
        SupportAgentPresence.updated_at.desc(),
        SupportAgentPresence.id,
    )
    return list(session.scalars(statement).all())


def list_available_agent_presence(
    session: Session,
    heartbeat_cutoff: datetime,
) -> list[SupportAgentPresence]:
    statement = (
        select(SupportAgentPresence)
        .where(SupportAgentPresence.presence_status == "online")
        .where(SupportAgentPresence.last_heartbeat_at >= heartbeat_cutoff)
        .where(SupportAgentPresence.active_session_count < SupportAgentPresence.max_active_sessions)
        .order_by(
            SupportAgentPresence.active_session_count,
            SupportAgentPresence.last_heartbeat_at.desc(),
            SupportAgentPresence.id,
        )
    )
    return list(session.scalars(statement).all())
