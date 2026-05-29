from pathlib import Path

from sqlalchemy import create_engine, inspect

from app.core.config import load_settings
from app.domains.support.models.support import SupportConversation, SupportMessage


def test_support_models_are_bound_to_expected_tables() -> None:
    assert SupportConversation.__tablename__ == "d2c_support_conversations"
    assert SupportMessage.__tablename__ == "d2c_support_messages"

    conversation_columns = set(SupportConversation.__table__.columns.keys())
    assert {
        "id",
        "conversation_code",
        "customer_id",
        "anonymous_id",
        "session_code",
        "contact_name",
        "contact_email",
        "contact_phone",
        "topic",
        "related_order_no",
        "status",
        "source",
        "conversation_token_hash",
        "created_at",
        "updated_at",
        "closed_at",
    }.issubset(conversation_columns)

    message_columns = set(SupportMessage.__table__.columns.keys())
    assert {
        "id",
        "conversation_id",
        "message_code",
        "sender_type",
        "body",
        "visibility",
        "created_at",
    }.issubset(message_columns)


def test_support_tables_exist_in_database() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)

        assert "d2c_support_conversations" in inspector.get_table_names()
        assert "d2c_support_messages" in inspector.get_table_names()

        conversation_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_conversations")
        }
        assert {
            "conversation_code",
            "customer_id",
            "anonymous_id",
            "session_code",
            "contact_email",
            "contact_phone",
            "topic",
            "related_order_no",
            "status",
            "source",
            "conversation_token_hash",
            "closed_at",
        }.issubset(conversation_columns)

        message_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_messages")
        }
        assert {
            "conversation_id",
            "message_code",
            "sender_type",
            "body",
            "visibility",
        }.issubset(message_columns)

        conversation_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_support_conversations")
        }
        assert "d2c_customers" in conversation_fk_targets

        message_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_support_messages")
        }
        assert "d2c_support_conversations" in message_fk_targets

        conversation_unique_names = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_support_conversations")
        }
        assert "uq_d2c_support_conv_code" in conversation_unique_names
        assert "uq_d2c_support_conv_token_hash" in conversation_unique_names

        message_unique_names = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_support_messages")
        }
        assert "uq_d2c_support_msg_code" in message_unique_names
    finally:
        engine.dispose()


def test_support_migration_registers_page_and_tables() -> None:
    migration_text = Path("alembic/versions/0038_support.py").read_text(encoding="utf-8")

    for token in (
        "customer_service",
        "/support",
        "客户服务",
        "auth_required",
        "d2c_support_conversations",
        "d2c_support_messages",
        "conversation_token_hash",
        "fk_d2c_support_conv_customer",
        "fk_d2c_support_msg_conv",
    ):
        assert token in migration_text


def test_support_model_is_registered_for_alembic_metadata() -> None:
    env_text = Path("alembic/env.py").read_text(encoding="utf-8")

    assert "from app.domains.support.models import support as support_models" in env_text
