"""Storefront live support session service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.customers.models.customer import Customer
from app.domains.customers.repos.customer_repo import get_active_customer_by_session_token_hash
from app.domains.support.contracts.storefront_support_live_contract import (
    SupportLiveAgentSummary,
    SupportLiveAvailabilityResponse,
    SupportLiveEndRequest,
    SupportLiveMessageCreateRequest,
    SupportLiveMessageResponse,
    SupportLiveSessionCreateRequest,
    SupportLiveSessionResponse,
)
from app.domains.support.models.support import (
    SupportContact,
    SupportConversation,
    SupportConversationEvent,
    SupportLiveSession,
    SupportMessage,
)
from app.domains.support.repos.support_repo import (
    count_live_sessions_by_status,
    create_contact,
    create_conversation,
    create_event,
    create_live_session,
    create_message,
    get_contact_by_customer_id,
    get_contact_by_email,
    get_contact_by_phone,
    get_live_session_by_code,
    list_available_agent_presence,
    list_messages_for_conversation,
)
from app.security.passwords import generate_session_token, hash_session_token

LIVE_HEARTBEAT_TTL_SECONDS = 300
LIVE_SYSTEM_WAITING_MESSAGE = "客服在线请求已收到，正在等待客服接入。"


class SupportLiveAuthError(Exception):
    pass


class SupportLiveConflictError(Exception):
    pass


class SupportLiveNotFoundError(Exception):
    pass


class SupportLiveValidationError(Exception):
    pass


def _new_code(prefix: str) -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_part}-{uuid4().hex[:12].upper()}"


def _new_contact_code() -> str:
    return _new_code("SUPCT")


def _new_conversation_code() -> str:
    return _new_code("SUP")


def _new_event_code() -> str:
    return _new_code("SUPEVT")


def _new_message_code() -> str:
    return _new_code("SUPMSG")


def _new_live_session_code() -> str:
    return _new_code("LIVE")


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
        raise SupportLiveValidationError("support_live_message_required")
    return normalized


def _authenticate_optional_customer(
    session: Session,
    access_token: str | None,
) -> Customer | None:
    if access_token is None:
        return None

    customer = get_active_customer_by_session_token_hash(
        session,
        hash_session_token(access_token),
        datetime.now(UTC),
    )
    if customer is None:
        raise SupportLiveAuthError("customer_auth_required")
    return customer


def _heartbeat_cutoff(now: datetime) -> datetime:
    return now - timedelta(seconds=LIVE_HEARTBEAT_TTL_SECONDS)


def _available_agent_count(session: Session, now: datetime) -> int:
    return len(list_available_agent_presence(session, _heartbeat_cutoff(now)))


def get_support_live_availability(session: Session) -> SupportLiveAvailabilityResponse:
    now = datetime.now(UTC)
    available_count = _available_agent_count(session, now)
    waiting_count = count_live_sessions_by_status(session, "waiting")
    active_count = count_live_sessions_by_status(session, "active")

    return SupportLiveAvailabilityResponse(
        availability_status="online" if available_count > 0 else "offline",
        available_agent_count=available_count,
        waiting_session_count=waiting_count,
        active_session_count=active_count,
        message="客服在线，可以开始咨询。"
        if available_count > 0
        else "当前客服离线，请使用留言咨询。",
    )


def _resolve_contact(
    session: Session,
    *,
    customer: Customer | None,
    anonymous_id: str | None,
    contact_name: str | None,
    contact_email: str | None,
    contact_phone: str | None,
    now: datetime,
) -> SupportContact:
    if customer is not None:
        contact = get_contact_by_customer_id(session, customer.id)
        if contact is None:
            return create_contact(
                session,
                SupportContact(
                    contact_code=_new_contact_code(),
                    customer_id=customer.id,
                    anonymous_id=anonymous_id,
                    contact_name=contact_name or customer.display_name,
                    contact_email=contact_email or customer.email,
                    contact_phone=contact_phone or customer.phone,
                    source="storefront",
                    first_seen_at=now,
                    last_seen_at=now,
                ),
            )

        contact.anonymous_id = anonymous_id or contact.anonymous_id
        contact.contact_name = contact_name or customer.display_name or contact.contact_name
        contact.contact_email = contact_email or customer.email or contact.contact_email
        contact.contact_phone = contact_phone or customer.phone or contact.contact_phone
        contact.last_seen_at = now
        contact.updated_at = now
        session.flush()
        return contact

    contact = None
    if contact_email is not None:
        contact = get_contact_by_email(session, contact_email)
    if contact is None and contact_phone is not None:
        contact = get_contact_by_phone(session, contact_phone)

    if contact is None:
        return create_contact(
            session,
            SupportContact(
                contact_code=_new_contact_code(),
                customer_id=None,
                anonymous_id=anonymous_id,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                source="storefront",
                first_seen_at=now,
                last_seen_at=now,
            ),
        )

    contact.anonymous_id = anonymous_id or contact.anonymous_id
    contact.contact_name = contact_name or contact.contact_name
    contact.contact_email = contact_email or contact.contact_email
    contact.contact_phone = contact_phone or contact.contact_phone
    contact.last_seen_at = now
    contact.updated_at = now
    session.flush()
    return contact


def _create_event(
    session: Session,
    *,
    conversation: SupportConversation,
    event_type: str,
    actor_type: str,
    message: SupportMessage | None = None,
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
            event_type=event_type,
            message_id=message.id if message is not None else None,
            from_status=from_status,
            to_status=to_status,
            payload_json=payload or {},
        ),
    )


def _message_schema(message: SupportMessage) -> SupportLiveMessageResponse:
    return SupportLiveMessageResponse(
        message_code=message.message_code,
        sender_type=message.sender_type,
        agent_code=message.agent.agent_code if message.agent is not None else None,
        body=message.body,
        created_at=message.created_at,
    )


def _agent_schema(live_session: SupportLiveSession) -> SupportLiveAgentSummary | None:
    if live_session.assigned_agent is None:
        return None

    return SupportLiveAgentSummary(
        agent_code=live_session.assigned_agent.agent_code,
        display_name=live_session.assigned_agent.display_name,
    )


def _session_schema(
    session: Session,
    live_session: SupportLiveSession,
    *,
    session_token: str | None = None,
) -> SupportLiveSessionResponse:
    messages = [
        message
        for message in list_messages_for_conversation(session, live_session.conversation_id)
        if message.visibility == "public"
    ]
    return SupportLiveSessionResponse(
        session_code=live_session.session_code,
        session_token=session_token,
        conversation_code=live_session.conversation.conversation_code,
        status=live_session.status,
        assigned_agent=_agent_schema(live_session),
        started_at=live_session.started_at,
        accepted_at=live_session.accepted_at,
        ended_at=live_session.ended_at,
        last_message_at=live_session.last_message_at,
        messages=[_message_schema(message) for message in messages],
    )


def create_support_live_session(
    session: Session,
    access_token: str | None,
    payload: SupportLiveSessionCreateRequest,
) -> SupportLiveSessionResponse:
    customer = _authenticate_optional_customer(session, access_token)
    now = datetime.now(UTC)

    if _available_agent_count(session, now) == 0:
        raise SupportLiveConflictError("support_live_unavailable")

    opening_message = _normalize_body(payload.opening_message)
    live_token: str | None = None
    live_token_hash: str | None = None

    if customer is None:
        live_token = generate_session_token()
        live_token_hash = hash_session_token(live_token)

    contact_name = _normalize_text(payload.contact_name) or (
        customer.display_name if customer is not None else None
    )
    contact_email = _normalize_email(payload.contact_email) or (
        customer.email if customer is not None else None
    )
    contact_phone = _normalize_text(payload.contact_phone) or (
        customer.phone if customer is not None else None
    )
    anonymous_id = _normalize_text(payload.anonymous_id)

    contact = _resolve_contact(
        session,
        customer=customer,
        anonymous_id=anonymous_id,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        now=now,
    )

    conversation = create_conversation(
        session,
        SupportConversation(
            conversation_code=_new_conversation_code(),
            customer_id=customer.id if customer is not None else None,
            contact_id=contact.id,
            anonymous_id=anonymous_id,
            session_code=_normalize_text(payload.session_code),
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            topic="other",
            related_order_no=None,
            status="pending_agent",
            priority="normal",
            source="storefront",
            conversation_token_hash=live_token_hash,
            last_message_at=now,
            last_customer_message_at=now,
            last_system_message_at=now,
            created_at=now,
            updated_at=now,
        ),
    )

    live_session = create_live_session(
        session,
        SupportLiveSession(
            session_code=_new_live_session_code(),
            conversation_id=conversation.id,
            customer_id=customer.id if customer is not None else None,
            anonymous_id=anonymous_id,
            visitor_session_code=_normalize_text(payload.session_code),
            status="waiting",
            source="storefront_widget",
            session_token_hash=live_token_hash,
            started_at=now,
            last_customer_seen_at=now,
            last_message_at=now,
            created_at=now,
            updated_at=now,
        ),
    )

    _create_event(
        session,
        conversation=conversation,
        event_type="live_session_started",
        actor_type="customer",
        from_status=None,
        to_status=conversation.status,
        payload={"live_session_code": live_session.session_code},
    )

    customer_message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            message_code=_new_message_code(),
            sender_type="customer",
            message_kind="text",
            body=opening_message,
            visibility="public",
            created_at=now,
        ),
    )
    _create_event(
        session,
        conversation=conversation,
        event_type="customer_message",
        actor_type="customer",
        message=customer_message,
        to_status=conversation.status,
        payload={"live_session_code": live_session.session_code},
    )

    system_message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            message_code=_new_message_code(),
            sender_type="system",
            message_kind="text",
            body=LIVE_SYSTEM_WAITING_MESSAGE,
            visibility="public",
            created_at=now,
        ),
    )
    _create_event(
        session,
        conversation=conversation,
        event_type="system_message",
        actor_type="system",
        message=system_message,
        to_status=conversation.status,
        payload={"live_session_code": live_session.session_code},
    )

    session.commit()
    return _session_schema(session, live_session, session_token=live_token)


def _authorize_live_access(
    live_session: SupportLiveSession,
    customer: Customer | None,
    session_token: str | None,
) -> None:
    if live_session.customer_id is not None:
        if customer is None:
            raise SupportLiveAuthError("customer_auth_required")
        if customer.id != live_session.customer_id:
            raise SupportLiveNotFoundError("support_live_session_not_found")
        return

    if live_session.session_token_hash is None:
        raise SupportLiveAuthError("support_live_session_token_required")

    if session_token is None:
        raise SupportLiveAuthError("support_live_session_token_required")

    if hash_session_token(session_token) != live_session.session_token_hash:
        raise SupportLiveAuthError("support_live_session_token_invalid")


def get_support_live_session(
    session: Session,
    access_token: str | None,
    session_code: str,
    session_token: str | None,
) -> SupportLiveSessionResponse:
    customer = _authenticate_optional_customer(session, access_token)
    live_session = get_live_session_by_code(session, session_code)

    if live_session is None:
        raise SupportLiveNotFoundError("support_live_session_not_found")

    _authorize_live_access(live_session, customer, session_token)
    return _session_schema(session, live_session)


def add_support_live_message(
    session: Session,
    access_token: str | None,
    session_code: str,
    payload: SupportLiveMessageCreateRequest,
) -> SupportLiveSessionResponse:
    customer = _authenticate_optional_customer(session, access_token)
    live_session = get_live_session_by_code(session, session_code)

    if live_session is None:
        raise SupportLiveNotFoundError("support_live_session_not_found")

    _authorize_live_access(live_session, customer, payload.session_token)

    if live_session.status not in {"waiting", "active"}:
        raise SupportLiveConflictError("support_live_session_closed")

    now = datetime.now(UTC)
    conversation = live_session.conversation
    from_status = conversation.status
    message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            message_code=_new_message_code(),
            sender_type="customer",
            message_kind="text",
            body=_normalize_body(payload.body),
            visibility="public",
            created_at=now,
        ),
    )

    conversation.status = "pending_agent"
    conversation.last_message_at = now
    conversation.last_customer_message_at = now
    conversation.updated_at = now
    live_session.last_customer_seen_at = now
    live_session.last_message_at = now
    live_session.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        event_type="customer_message",
        actor_type="customer",
        message=message,
        from_status=from_status,
        to_status=conversation.status,
        payload={"live_session_code": live_session.session_code},
    )

    session.commit()
    return _session_schema(session, live_session)


def end_support_live_session(
    session: Session,
    access_token: str | None,
    session_code: str,
    payload: SupportLiveEndRequest,
) -> SupportLiveSessionResponse:
    customer = _authenticate_optional_customer(session, access_token)
    live_session = get_live_session_by_code(session, session_code)

    if live_session is None:
        raise SupportLiveNotFoundError("support_live_session_not_found")

    _authorize_live_access(live_session, customer, payload.session_token)

    if live_session.status not in {"waiting", "active"}:
        raise SupportLiveConflictError("support_live_session_closed")

    now = datetime.now(UTC)
    conversation = live_session.conversation
    from_status = conversation.status
    live_session.status = "missed" if live_session.status == "waiting" else "ended"
    live_session.ended_at = now
    live_session.updated_at = now
    conversation.status = "closed"
    conversation.closed_at = now
    conversation.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        event_type="live_session_ended",
        actor_type="customer",
        from_status=from_status,
        to_status="closed",
        payload={
            "live_session_code": live_session.session_code,
            "live_status": live_session.status,
            "reason": payload.reason,
        },
    )

    session.commit()
    return _session_schema(session, live_session)
