"""Repositories for storefront support conversations."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domains.support.models.support import SupportConversation, SupportMessage

SupportConversationWithCount = tuple[SupportConversation, int]


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
