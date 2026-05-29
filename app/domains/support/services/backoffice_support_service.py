"""Backoffice support workbench service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.support.contracts.backoffice_support_contract import (
    BackofficeSupportAgent,
    BackofficeSupportAgentCreateRequest,
    BackofficeSupportAgentsResponse,
    BackofficeSupportAssignRequest,
    BackofficeSupportCloseRequest,
    BackofficeSupportContact,
    BackofficeSupportConversationListResponse,
    BackofficeSupportConversationResponse,
    BackofficeSupportConversationSummary,
    BackofficeSupportEvent,
    BackofficeSupportEventsResponse,
    BackofficeSupportMessage,
    BackofficeSupportMessageCreateRequest,
)
from app.domains.support.models.support import (
    SupportAgentProfile,
    SupportContact,
    SupportConversation,
    SupportConversationAssignment,
    SupportConversationEvent,
    SupportMessage,
)
from app.domains.support.repos.support_repo import (
    create_agent_profile,
    create_assignment,
    create_event,
    create_message,
    get_active_agent_by_code,
    get_agent_by_code,
    get_conversation_by_code,
    list_agent_profiles,
    list_backoffice_conversations,
    list_events_for_conversation,
    list_messages_for_conversation,
    replace_active_assignments,
)


class BackofficeSupportAuthError(Exception):
    pass


class BackofficeSupportConflictError(Exception):
    pass


class BackofficeSupportNotFoundError(Exception):
    pass


class BackofficeSupportValidationError(Exception):
    pass


def _new_code(prefix: str) -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_part}-{uuid4().hex[:12].upper()}"


def _new_agent_code() -> str:
    return _new_code("AGENT")


def _new_message_code() -> str:
    return _new_code("SUPMSG")


def _new_assignment_code() -> str:
    return _new_code("SUPASN")


def _new_event_code() -> str:
    return _new_code("SUPEVT")


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_email(value: str | None) -> str | None:
    normalized = _normalize_text(value)
    return normalized.lower() if normalized is not None else None


def _normalize_body(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise BackofficeSupportValidationError("support_message_required")
    return normalized


def require_active_agent(session: Session, agent_code: str | None) -> SupportAgentProfile:
    normalized = _normalize_text(agent_code)
    if normalized is None:
        raise BackofficeSupportAuthError("support_agent_required")

    agent = get_active_agent_by_code(session, normalized)
    if agent is None:
        raise BackofficeSupportAuthError("support_agent_required")
    return agent


def _agent_schema(agent: SupportAgentProfile | None) -> BackofficeSupportAgent | None:
    if agent is None:
        return None
    return BackofficeSupportAgent(
        agent_code=agent.agent_code,
        display_name=agent.display_name,
        email=agent.email,
        status=agent.status,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


def _contact_schema(contact: SupportContact | None) -> BackofficeSupportContact | None:
    if contact is None:
        return None
    return BackofficeSupportContact(
        contact_code=contact.contact_code,
        customer_id=contact.customer_id,
        anonymous_id=contact.anonymous_id,
        contact_name=contact.contact_name,
        contact_email=contact.contact_email,
        contact_phone=contact.contact_phone,
        source=contact.source,
        first_seen_at=contact.first_seen_at,
        last_seen_at=contact.last_seen_at,
    )


def _message_schema(message: SupportMessage) -> BackofficeSupportMessage:
    return BackofficeSupportMessage(
        message_code=message.message_code,
        sender_type=message.sender_type,
        agent_code=message.agent.agent_code if message.agent is not None else None,
        body=message.body,
        visibility=message.visibility,
        message_kind=message.message_kind,
        created_at=message.created_at,
    )


def _conversation_summary_schema(
    conversation: SupportConversation,
    message_count: int,
) -> BackofficeSupportConversationSummary:
    return BackofficeSupportConversationSummary(
        conversation_code=conversation.conversation_code,
        customer_id=conversation.customer_id,
        contact=_contact_schema(conversation.contact),
        assigned_agent=_agent_schema(conversation.assigned_agent),
        topic=conversation.topic,
        related_order_no=conversation.related_order_no,
        status=conversation.status,
        priority=conversation.priority,
        source=conversation.source,
        contact_name=conversation.contact_name,
        contact_email=conversation.contact_email,
        contact_phone=conversation.contact_phone,
        message_count=message_count,
        last_message_at=conversation.last_message_at,
        last_customer_message_at=conversation.last_customer_message_at,
        last_agent_message_at=conversation.last_agent_message_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        closed_at=conversation.closed_at,
    )


def _conversation_detail_schema(
    session: Session,
    conversation: SupportConversation,
) -> BackofficeSupportConversationResponse:
    messages = [
        _message_schema(message)
        for message in list_messages_for_conversation(session, conversation.id)
    ]
    summary = _conversation_summary_schema(conversation, len(messages))
    return BackofficeSupportConversationResponse(
        **summary.model_dump(),
        messages=messages,
    )


def _event_schema(event: SupportConversationEvent) -> BackofficeSupportEvent:
    return BackofficeSupportEvent(
        event_code=event.event_code,
        event_type=event.event_type,
        actor_type=event.actor_type,
        actor_agent_code=event.actor_agent.agent_code if event.actor_agent is not None else None,
        message_code=event.message.message_code if event.message is not None else None,
        assignment_code=event.assignment.assignment_code if event.assignment is not None else None,
        from_status=event.from_status,
        to_status=event.to_status,
        payload=event.payload_json,
        created_at=event.created_at,
    )


def _create_event(
    session: Session,
    *,
    conversation: SupportConversation,
    actor_type: str,
    event_type: str,
    actor_agent: SupportAgentProfile | None = None,
    message: SupportMessage | None = None,
    assignment: SupportConversationAssignment | None = None,
    from_status: str | None = None,
    to_status: str | None = None,
    payload: dict[str, object] | None = None,
) -> SupportConversationEvent:
    return create_event(
        session,
        SupportConversationEvent(
            event_code=_new_event_code(),
            conversation_id=conversation.id,
            actor_type=actor_type,
            actor_agent_id=actor_agent.id if actor_agent is not None else None,
            event_type=event_type,
            message_id=message.id if message is not None else None,
            assignment_id=assignment.id if assignment is not None else None,
            from_status=from_status,
            to_status=to_status,
            payload_json=payload or {},
        ),
    )


def create_backoffice_support_agent(
    session: Session,
    payload: BackofficeSupportAgentCreateRequest,
) -> BackofficeSupportAgent:
    agent_code = _normalize_text(payload.agent_code) or _new_agent_code()
    email = _normalize_email(payload.email)

    if get_agent_by_code(session, agent_code) is not None:
        raise BackofficeSupportConflictError("support_agent_code_already_exists")

    now = datetime.now(UTC)
    agent = create_agent_profile(
        session,
        SupportAgentProfile(
            agent_code=agent_code,
            display_name=payload.display_name.strip(),
            email=email,
            status="active",
            created_at=now,
            updated_at=now,
        ),
    )
    session.commit()
    schema = _agent_schema(agent)
    assert schema is not None
    return schema


def list_backoffice_support_agents(session: Session) -> BackofficeSupportAgentsResponse:
    agents = [_agent_schema(agent) for agent in list_agent_profiles(session)]
    return BackofficeSupportAgentsResponse(
        agents=[agent for agent in agents if agent is not None],
        count=len(agents),
    )


def list_backoffice_support_conversations(
    session: Session,
    *,
    status_filter: str | None = None,
    topic: str | None = None,
    assigned_agent_code: str | None = None,
) -> BackofficeSupportConversationListResponse:
    assigned_agent_id: int | None = None
    if assigned_agent_code is not None:
        agent = get_agent_by_code(session, assigned_agent_code)
        if agent is None:
            return BackofficeSupportConversationListResponse(count=0)
        assigned_agent_id = agent.id

    rows = list_backoffice_conversations(
        session,
        status_filter=status_filter,
        topic=topic,
        assigned_agent_id=assigned_agent_id,
    )
    conversations = [
        _conversation_summary_schema(conversation, message_count)
        for conversation, message_count in rows
    ]
    return BackofficeSupportConversationListResponse(
        conversations=conversations,
        count=len(conversations),
    )


def get_backoffice_support_conversation(
    session: Session,
    conversation_code: str,
) -> BackofficeSupportConversationResponse:
    conversation = get_conversation_by_code(session, conversation_code)
    if conversation is None:
        raise BackofficeSupportNotFoundError("support_conversation_not_found")
    return _conversation_detail_schema(session, conversation)


def assign_backoffice_support_conversation(
    session: Session,
    conversation_code: str,
    actor_agent_code: str | None,
    payload: BackofficeSupportAssignRequest,
) -> BackofficeSupportConversationResponse:
    actor_agent = require_active_agent(session, actor_agent_code)
    target_agent = require_active_agent(session, payload.agent_code)
    conversation = get_conversation_by_code(session, conversation_code)

    if conversation is None:
        raise BackofficeSupportNotFoundError("support_conversation_not_found")

    if conversation.status == "closed":
        raise BackofficeSupportConflictError("support_conversation_closed")

    now = datetime.now(UTC)
    replace_active_assignments(session, conversation.id, now)
    assignment = create_assignment(
        session,
        SupportConversationAssignment(
            assignment_code=_new_assignment_code(),
            conversation_id=conversation.id,
            agent_id=target_agent.id,
            assigned_by_agent_id=actor_agent.id,
            status="active",
            assigned_at=now,
        ),
    )
    conversation.assigned_agent_id = target_agent.id
    conversation.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        actor_type="agent",
        actor_agent=actor_agent,
        event_type="assigned",
        assignment=assignment,
        from_status=conversation.status,
        to_status=conversation.status,
        payload={"assigned_agent_code": target_agent.agent_code},
    )

    session.commit()
    return _conversation_detail_schema(session, conversation)


def add_backoffice_support_message(
    session: Session,
    conversation_code: str,
    agent_code: str | None,
    payload: BackofficeSupportMessageCreateRequest,
) -> BackofficeSupportConversationResponse:
    agent = require_active_agent(session, agent_code)
    conversation = get_conversation_by_code(session, conversation_code)

    if conversation is None:
        raise BackofficeSupportNotFoundError("support_conversation_not_found")

    if conversation.status == "closed":
        raise BackofficeSupportConflictError("support_conversation_closed")

    body = _normalize_body(payload.body)
    now = datetime.now(UTC)
    from_status = conversation.status

    message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            agent_id=agent.id,
            message_code=_new_message_code(),
            sender_type="agent",
            message_kind="note" if payload.visibility == "internal" else "text",
            body=body,
            visibility=payload.visibility,
            created_at=now,
        ),
    )

    conversation.assigned_agent_id = agent.id
    conversation.status = (
        "pending_customer" if payload.visibility == "public" else conversation.status
    )
    conversation.last_message_at = now
    if payload.visibility == "public":
        conversation.last_agent_message_at = now
    conversation.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        actor_type="agent",
        actor_agent=agent,
        event_type="agent_message" if payload.visibility == "public" else "internal_note",
        message=message,
        from_status=from_status,
        to_status=conversation.status,
    )

    session.commit()
    return _conversation_detail_schema(session, conversation)


def close_backoffice_support_conversation(
    session: Session,
    conversation_code: str,
    agent_code: str | None,
    payload: BackofficeSupportCloseRequest,
) -> BackofficeSupportConversationResponse:
    agent = require_active_agent(session, agent_code)
    conversation = get_conversation_by_code(session, conversation_code)

    if conversation is None:
        raise BackofficeSupportNotFoundError("support_conversation_not_found")

    if conversation.status == "closed":
        raise BackofficeSupportConflictError("support_conversation_closed")

    now = datetime.now(UTC)
    from_status = conversation.status
    conversation.status = "closed"
    conversation.closed_at = now
    conversation.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        actor_type="agent",
        actor_agent=agent,
        event_type="closed",
        from_status=from_status,
        to_status="closed",
        payload={"reason": payload.reason} if payload.reason else {},
    )

    session.commit()
    return _conversation_detail_schema(session, conversation)


def list_backoffice_support_events(
    session: Session,
    conversation_code: str,
) -> BackofficeSupportEventsResponse:
    conversation = get_conversation_by_code(session, conversation_code)
    if conversation is None:
        raise BackofficeSupportNotFoundError("support_conversation_not_found")

    events = [
        _event_schema(event) for event in list_events_for_conversation(session, conversation.id)
    ]
    return BackofficeSupportEventsResponse(
        events=events,
        count=len(events),
    )
