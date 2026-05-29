from pathlib import Path

from sqlalchemy import create_engine, inspect

from app.core.config import load_settings
from app.domains.support.models.support import (
    SupportAgentProfile,
    SupportContact,
    SupportConversation,
    SupportConversationAssignment,
    SupportConversationEvent,
    SupportMessage,
)


def test_support_workbench_models_are_bound_to_expected_tables() -> None:
    assert SupportContact.__tablename__ == "d2c_support_contacts"
    assert SupportAgentProfile.__tablename__ == "d2c_support_agent_profiles"
    assert SupportConversation.__tablename__ == "d2c_support_conversations"
    assert SupportMessage.__tablename__ == "d2c_support_messages"
    assert SupportConversationAssignment.__tablename__ == "d2c_support_conversation_assignments"
    assert SupportConversationEvent.__tablename__ == "d2c_support_conversation_events"

    assert "contact_id" in SupportConversation.__table__.columns
    assert "assigned_agent_id" in SupportConversation.__table__.columns
    assert "priority" in SupportConversation.__table__.columns
    assert "last_message_at" in SupportConversation.__table__.columns
    assert "agent_id" in SupportMessage.__table__.columns
    assert "message_kind" in SupportMessage.__table__.columns


def test_support_workbench_tables_exist_in_database() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        for table in (
            "d2c_support_contacts",
            "d2c_support_agent_profiles",
            "d2c_support_conversation_assignments",
            "d2c_support_conversation_events",
        ):
            assert table in table_names

        conversation_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_conversations")
        }
        assert {
            "contact_id",
            "assigned_agent_id",
            "priority",
            "last_message_at",
            "last_customer_message_at",
            "last_agent_message_at",
            "last_system_message_at",
        }.issubset(conversation_columns)

        message_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_messages")
        }
        assert {"agent_id", "message_kind"}.issubset(message_columns)

        event_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_conversation_events")
        }
        assert {
            "event_code",
            "conversation_id",
            "actor_type",
            "event_type",
            "message_id",
            "assignment_id",
            "from_status",
            "to_status",
            "payload_json",
        }.issubset(event_columns)
    finally:
        engine.dispose()


def test_support_workbench_migration_contains_owner_model() -> None:
    text = Path("alembic/versions/0039_support_wb.py").read_text(encoding="utf-8")

    for token in (
        "d2c_support_contacts",
        "d2c_support_agent_profiles",
        "d2c_support_conversation_assignments",
        "d2c_support_conversation_events",
        "pending_agent",
        "pending_customer",
        "internal",
        "message_kind",
        "contact_id",
        "assigned_agent_id",
    ):
        assert token in text
