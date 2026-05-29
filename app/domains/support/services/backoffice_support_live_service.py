"""Backoffice live support session service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.support.contracts.backoffice_support_live_contract import (
    BackofficeSupportAgentPresenceResponse,
    BackofficeSupportAgentPresenceUpdateRequest,
    BackofficeSupportLiveEndRequest,
    BackofficeSupportLiveMessage,
    BackofficeSupportLiveMessageCreateRequest,
    BackofficeSupportLivePresenceListResponse,
    BackofficeSupportLiveSessionResponse,
    BackofficeSupportLiveSessionsResponse,
    BackofficeSupportLiveSessionSummary,
)
from app.domains.support.models.support import (
    SupportAgentPresence,
    SupportAgentProfile,
    SupportConversation,
    SupportConversationAssignment,
    SupportConversationEvent,
    SupportLiveSession,
    SupportMessage,
)
from app.domains.support.repos.support_repo import (
    count_active_live_sessions_for_agent,
    create_agent_presence,
    create_assignment,
    create_event,
    create_message,
    get_agent_by_code,
    get_agent_presence_by_agent_id,
    get_live_session_by_code,
    list_agent_presence,
    list_live_sessions,
    replace_active_assignments,
)
from app.domains.support.services.backoffice_support_service import (
    BackofficeSupportConflictError,
    BackofficeSupportNotFoundError,
    BackofficeSupportValidationError,
    require_active_agent,
)

LIVE_HEARTBEAT_TTL_SECONDS = 300


def _new_code(prefix: str) -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_part}-{uuid4().hex[:12].upper()}"


def _new_assignment_code() -> str:
    return _new_code("SUPASN")


def _new_event_code() -> str:
    return _new_code("SUPEVT")


def _new_message_code() -> str:
    return _new_code("SUPMSG")


def _normalize_body(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise BackofficeSupportValidationError("support_message_required")
    return normalized


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


def _presence_schema(presence: SupportAgentPresence) -> BackofficeSupportAgentPresenceResponse:
    return BackofficeSupportAgentPresenceResponse(
        agent_code=presence.agent_code,
        display_name=presence.agent.display_name,
        presence_status=presence.presence_status,
        max_active_sessions=presence.max_active_sessions,
        active_session_count=presence.active_session_count,
        last_heartbeat_at=presence.last_heartbeat_at,
        updated_at=presence.updated_at,
    )


def _heartbeat_cutoff(now: datetime) -> datetime:
    return now - timedelta(seconds=LIVE_HEARTBEAT_TTL_SECONDS)


def update_backoffice_support_agent_presence(
    session: Session,
    agent_code: str,
    payload: BackofficeSupportAgentPresenceUpdateRequest,
) -> BackofficeSupportAgentPresenceResponse:
    agent = require_active_agent(session, agent_code)
    now = datetime.now(UTC)
    active_count = count_active_live_sessions_for_agent(session, agent.id)
    presence = get_agent_presence_by_agent_id(session, agent.id)

    if presence is None:
        presence = create_agent_presence(
            session,
            SupportAgentPresence(
                agent_id=agent.id,
                agent_code=agent.agent_code,
                presence_status=payload.presence_status,
                max_active_sessions=payload.max_active_sessions,
                active_session_count=active_count,
                last_heartbeat_at=now if payload.presence_status == "online" else None,
                created_at=now,
                updated_at=now,
            ),
        )
    else:
        presence.agent_code = agent.agent_code
        presence.presence_status = payload.presence_status
        presence.max_active_sessions = payload.max_active_sessions
        presence.active_session_count = active_count
        presence.last_heartbeat_at = now if payload.presence_status == "online" else None
        presence.updated_at = now
        session.flush()

    session.commit()
    return _presence_schema(presence)


def list_backoffice_support_agent_presence(
    session: Session,
) -> BackofficeSupportLivePresenceListResponse:
    now = datetime.now(UTC)
    cutoff = _heartbeat_cutoff(now)
    presences = list_agent_presence(session)

    for presence in presences:
        if (
            presence.presence_status == "online"
            and presence.last_heartbeat_at is not None
            and presence.last_heartbeat_at < cutoff
        ):
            presence.presence_status = "offline"
            presence.updated_at = now
            session.flush()

    session.commit()

    schemas = [_presence_schema(presence) for presence in presences]
    return BackofficeSupportLivePresenceListResponse(agents=schemas, count=len(schemas))


def _message_schema(message: SupportMessage) -> BackofficeSupportLiveMessage:
    return BackofficeSupportLiveMessage(
        message_code=message.message_code,
        sender_type=message.sender_type,
        agent_code=message.agent.agent_code if message.agent is not None else None,
        body=message.body,
        created_at=message.created_at,
    )


def _session_summary_schema(
    live_session: SupportLiveSession,
) -> BackofficeSupportLiveSessionSummary:
    conversation = live_session.conversation
    agent = live_session.assigned_agent

    return BackofficeSupportLiveSessionSummary(
        session_code=live_session.session_code,
        conversation_code=conversation.conversation_code,
        customer_id=live_session.customer_id,
        anonymous_id=live_session.anonymous_id,
        contact_name=conversation.contact_name,
        contact_email=conversation.contact_email,
        contact_phone=conversation.contact_phone,
        status=live_session.status,
        assigned_agent_code=agent.agent_code if agent is not None else None,
        assigned_agent_name=agent.display_name if agent is not None else None,
        started_at=live_session.started_at,
        accepted_at=live_session.accepted_at,
        ended_at=live_session.ended_at,
        last_customer_seen_at=live_session.last_customer_seen_at,
        last_agent_seen_at=live_session.last_agent_seen_at,
        last_message_at=live_session.last_message_at,
    )


def _session_detail_schema(
    session: Session,
    live_session: SupportLiveSession,
) -> BackofficeSupportLiveSessionResponse:
    summary = _session_summary_schema(live_session)
    messages = [
        _message_schema(message)
        for message in list(live_session.conversation.messages)
        if message.visibility == "public"
    ]
    messages.sort(key=lambda message: (message.created_at, message.message_code))
    return BackofficeSupportLiveSessionResponse(
        **summary.model_dump(),
        messages=messages,
    )


def list_backoffice_support_live_sessions(
    session: Session,
    *,
    status_filter: str | None = None,
    assigned_agent_code: str | None = None,
) -> BackofficeSupportLiveSessionsResponse:
    assigned_agent_id: int | None = None
    if assigned_agent_code is not None:
        agent = get_agent_by_code(session, assigned_agent_code)
        if agent is None:
            return BackofficeSupportLiveSessionsResponse(count=0)
        assigned_agent_id = agent.id

    rows = list_live_sessions(
        session,
        status_filter=status_filter,
        assigned_agent_id=assigned_agent_id,
    )
    sessions = [_session_summary_schema(row) for row in rows]
    return BackofficeSupportLiveSessionsResponse(sessions=sessions, count=len(sessions))


def get_backoffice_support_live_session(
    session: Session,
    session_code: str,
) -> BackofficeSupportLiveSessionResponse:
    live_session = get_live_session_by_code(session, session_code)
    if live_session is None:
        raise BackofficeSupportNotFoundError("support_live_session_not_found")
    return _session_detail_schema(session, live_session)


def accept_backoffice_support_live_session(
    session: Session,
    session_code: str,
    agent_code: str | None,
) -> BackofficeSupportLiveSessionResponse:
    agent = require_active_agent(session, agent_code)
    live_session = get_live_session_by_code(session, session_code)

    if live_session is None:
        raise BackofficeSupportNotFoundError("support_live_session_not_found")

    if live_session.status != "waiting":
        raise BackofficeSupportConflictError("support_live_session_not_waiting")

    now = datetime.now(UTC)
    conversation = live_session.conversation
    replace_active_assignments(session, conversation.id, now)
    assignment = create_assignment(
        session,
        SupportConversationAssignment(
            assignment_code=_new_assignment_code(),
            conversation_id=conversation.id,
            agent_id=agent.id,
            assigned_by_agent_id=agent.id,
            status="active",
            assigned_at=now,
        ),
    )

    live_session.status = "active"
    live_session.assigned_agent_id = agent.id
    live_session.accepted_at = now
    live_session.last_agent_seen_at = now
    live_session.updated_at = now
    conversation.assigned_agent_id = agent.id
    conversation.updated_at = now

    session.flush()
    session.flush()
    presence = get_agent_presence_by_agent_id(session, agent.id)
    if presence is not None:
        presence.active_session_count = count_active_live_sessions_for_agent(session, agent.id)
        presence.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        actor_type="agent",
        actor_agent=agent,
        event_type="live_session_accepted",
        assignment=assignment,
        from_status=conversation.status,
        to_status=conversation.status,
        payload={"live_session_code": live_session.session_code},
    )

    session.commit()
    return _session_detail_schema(session, live_session)


def add_backoffice_support_live_message(
    session: Session,
    session_code: str,
    agent_code: str | None,
    payload: BackofficeSupportLiveMessageCreateRequest,
) -> BackofficeSupportLiveSessionResponse:
    agent = require_active_agent(session, agent_code)
    live_session = get_live_session_by_code(session, session_code)

    if live_session is None:
        raise BackofficeSupportNotFoundError("support_live_session_not_found")

    if live_session.status != "active":
        raise BackofficeSupportConflictError("support_live_session_not_active")

    now = datetime.now(UTC)
    conversation = live_session.conversation
    from_status = conversation.status
    message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            agent_id=agent.id,
            message_code=_new_message_code(),
            sender_type="agent",
            message_kind="text",
            body=_normalize_body(payload.body),
            visibility="public",
            created_at=now,
        ),
    )

    conversation.assigned_agent_id = agent.id
    conversation.status = "pending_customer"
    conversation.last_message_at = now
    conversation.last_agent_message_at = now
    conversation.updated_at = now
    live_session.assigned_agent_id = agent.id
    live_session.last_agent_seen_at = now
    live_session.last_message_at = now
    live_session.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        actor_type="agent",
        actor_agent=agent,
        event_type="agent_message",
        message=message,
        from_status=from_status,
        to_status=conversation.status,
        payload={"live_session_code": live_session.session_code},
    )

    session.commit()
    return _session_detail_schema(session, live_session)


def end_backoffice_support_live_session(
    session: Session,
    session_code: str,
    agent_code: str | None,
    payload: BackofficeSupportLiveEndRequest,
) -> BackofficeSupportLiveSessionResponse:
    agent = require_active_agent(session, agent_code)
    live_session = get_live_session_by_code(session, session_code)

    if live_session is None:
        raise BackofficeSupportNotFoundError("support_live_session_not_found")

    if live_session.status not in {"waiting", "active"}:
        raise BackofficeSupportConflictError("support_live_session_closed")

    now = datetime.now(UTC)
    conversation = live_session.conversation
    from_status = conversation.status
    live_session.status = "ended" if live_session.status == "active" else "missed"
    live_session.ended_at = now
    live_session.last_agent_seen_at = now
    live_session.updated_at = now
    conversation.status = "closed"
    conversation.closed_at = now
    conversation.updated_at = now

    presence = get_agent_presence_by_agent_id(session, agent.id)
    if presence is not None:
        presence.active_session_count = count_active_live_sessions_for_agent(session, agent.id)
        presence.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        actor_type="agent",
        actor_agent=agent,
        event_type="live_session_ended",
        from_status=from_status,
        to_status="closed",
        payload={
            "live_session_code": live_session.session_code,
            "live_status": live_session.status,
            "reason": payload.reason,
        },
    )

    session.commit()
    return _session_detail_schema(session, live_session)
