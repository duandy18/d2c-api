"""Storefront customer support conversation service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.customers.models.customer import Customer
from app.domains.customers.repos.customer_repo import get_active_customer_by_session_token_hash
from app.domains.support.contracts.storefront_support_contract import (
    SupportConversationCreateRequest,
    SupportConversationListResponse,
    SupportConversationResponse,
    SupportConversationSummary,
    SupportMessageCreateRequest,
    SupportMessageResponse,
)
from app.domains.support.models.support import (
    SupportContact,
    SupportConversation,
    SupportConversationEvent,
    SupportMessage,
)
from app.domains.support.repos.support_repo import (
    create_contact,
    create_conversation,
    create_event,
    create_message,
    get_contact_by_customer_id,
    get_contact_by_email,
    get_contact_by_phone,
    get_conversation_by_code,
    list_conversations_by_customer,
    list_messages_for_conversation,
)
from app.security.passwords import generate_session_token, hash_session_token

SYSTEM_CONFIRMATION_MESSAGE = "我们已收到您的消息，客服会尽快回复。"


class SupportAuthError(Exception):
    pass


class SupportValidationError(Exception):
    pass


class SupportNotFoundError(Exception):
    pass


class SupportConflictError(Exception):
    pass


def _new_code(prefix: str) -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"{prefix}-{date_part}-{uuid4().hex[:12].upper()}"


def _new_conversation_code() -> str:
    return _new_code("SUP")


def _new_message_code() -> str:
    return _new_code("SUPMSG")


def _new_contact_code() -> str:
    return _new_code("SUPCT")


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
        raise SupportValidationError("support_message_required")
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
        raise SupportAuthError("customer_auth_required")
    return customer


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
            contact = create_contact(
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
        else:
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


def _build_message_response(message: SupportMessage) -> SupportMessageResponse:
    return SupportMessageResponse(
        message_code=message.message_code,
        sender_type=message.sender_type,
        body=message.body,
        visibility=message.visibility,
        created_at=message.created_at,
    )


def _build_summary_response(
    conversation: SupportConversation,
    message_count: int,
) -> SupportConversationSummary:
    return SupportConversationSummary(
        conversation_code=conversation.conversation_code,
        topic=conversation.topic,
        related_order_no=conversation.related_order_no,
        status=conversation.status,
        source=conversation.source,
        contact_name=conversation.contact_name,
        contact_email=conversation.contact_email,
        contact_phone=conversation.contact_phone,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        closed_at=conversation.closed_at,
    )


def _build_conversation_response(
    session: Session,
    conversation: SupportConversation,
    *,
    conversation_token: str | None = None,
) -> SupportConversationResponse:
    messages = [
        message
        for message in list_messages_for_conversation(session, conversation.id)
        if message.visibility == "public"
    ]
    return SupportConversationResponse(
        conversation_code=conversation.conversation_code,
        topic=conversation.topic,
        related_order_no=conversation.related_order_no,
        status=conversation.status,
        source=conversation.source,
        contact_name=conversation.contact_name,
        contact_email=conversation.contact_email,
        contact_phone=conversation.contact_phone,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        closed_at=conversation.closed_at,
        conversation_token=conversation_token,
        messages=[_build_message_response(message) for message in messages],
    )


def _assert_anonymous_contact(payload: SupportConversationCreateRequest) -> None:
    contact_email = _normalize_email(payload.contact_email)
    contact_phone = _normalize_text(payload.contact_phone)
    if contact_email is None and contact_phone is None:
        raise SupportValidationError("support_contact_email_or_phone_required")


def create_support_conversation(
    session: Session,
    access_token: str | None,
    payload: SupportConversationCreateRequest,
) -> SupportConversationResponse:
    customer = _authenticate_optional_customer(session, access_token)
    message_body = _normalize_body(payload.message)

    conversation_token: str | None = None
    conversation_token_hash: str | None = None

    if customer is None:
        _assert_anonymous_contact(payload)
        conversation_token = generate_session_token()
        conversation_token_hash = hash_session_token(conversation_token)

    now = datetime.now(UTC)
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
            topic=payload.topic,
            related_order_no=_normalize_text(payload.related_order_no),
            status="pending_agent",
            priority="normal",
            source="storefront",
            conversation_token_hash=conversation_token_hash,
            last_message_at=now,
            last_customer_message_at=now,
            last_system_message_at=now,
            created_at=now,
            updated_at=now,
        ),
    )

    _create_event(
        session,
        conversation=conversation,
        event_type="conversation_created",
        actor_type="customer" if customer is not None else "system",
        from_status=None,
        to_status=conversation.status,
    )

    customer_message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            message_code=_new_message_code(),
            sender_type="customer",
            message_kind="text",
            body=message_body,
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
    )

    system_message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            message_code=_new_message_code(),
            sender_type="system",
            message_kind="text",
            body=SYSTEM_CONFIRMATION_MESSAGE,
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
    )

    session.commit()
    return _build_conversation_response(
        session,
        conversation,
        conversation_token=conversation_token,
    )


def list_support_conversations(
    session: Session,
    access_token: str | None,
) -> SupportConversationListResponse:
    customer = _authenticate_optional_customer(session, access_token)

    if customer is None:
        return SupportConversationListResponse(count=0)

    rows = list_conversations_by_customer(session, customer.id)
    conversations = [
        _build_summary_response(conversation, message_count) for conversation, message_count in rows
    ]
    return SupportConversationListResponse(
        conversations=conversations,
        count=len(conversations),
    )


def _authorize_conversation_access(
    conversation: SupportConversation,
    customer: Customer | None,
    conversation_token: str | None,
) -> None:
    if conversation.customer_id is not None:
        if customer is None:
            raise SupportAuthError("customer_auth_required")
        if conversation.customer_id != customer.id:
            raise SupportNotFoundError("support_conversation_not_found")
        return

    if conversation.conversation_token_hash is None:
        raise SupportAuthError("support_conversation_token_required")

    if conversation_token is None:
        raise SupportAuthError("support_conversation_token_required")

    if hash_session_token(conversation_token) != conversation.conversation_token_hash:
        raise SupportAuthError("support_conversation_token_invalid")


def get_support_conversation(
    session: Session,
    access_token: str | None,
    conversation_code: str,
    conversation_token: str | None,
) -> SupportConversationResponse:
    customer = _authenticate_optional_customer(session, access_token)
    conversation = get_conversation_by_code(session, conversation_code)

    if conversation is None:
        raise SupportNotFoundError("support_conversation_not_found")

    _authorize_conversation_access(conversation, customer, conversation_token)
    return _build_conversation_response(session, conversation)


def add_support_conversation_message(
    session: Session,
    access_token: str | None,
    conversation_code: str,
    payload: SupportMessageCreateRequest,
) -> SupportConversationResponse:
    customer = _authenticate_optional_customer(session, access_token)
    conversation = get_conversation_by_code(session, conversation_code)

    if conversation is None:
        raise SupportNotFoundError("support_conversation_not_found")

    _authorize_conversation_access(conversation, customer, payload.conversation_token)

    if conversation.status == "closed":
        raise SupportConflictError("support_conversation_closed")

    message_body = _normalize_body(payload.body)
    now = datetime.now(UTC)
    from_status = conversation.status

    message = create_message(
        session,
        SupportMessage(
            conversation_id=conversation.id,
            message_code=_new_message_code(),
            sender_type="customer",
            message_kind="text",
            body=message_body,
            visibility="public",
            created_at=now,
        ),
    )
    conversation.status = "pending_agent"
    conversation.last_message_at = now
    conversation.last_customer_message_at = now
    conversation.updated_at = now

    _create_event(
        session,
        conversation=conversation,
        event_type="customer_message",
        actor_type="customer",
        message=message,
        from_status=from_status,
        to_status=conversation.status,
    )

    session.commit()
    return _build_conversation_response(session, conversation)
