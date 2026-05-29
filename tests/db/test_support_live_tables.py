from pathlib import Path

from sqlalchemy import create_engine, inspect

from app.core.config import load_settings
from app.domains.support.models.support import SupportAgentPresence, SupportLiveSession


def test_support_live_models_are_bound_to_expected_tables() -> None:
    assert SupportLiveSession.__tablename__ == "d2c_support_live_sessions"
    assert SupportAgentPresence.__tablename__ == "d2c_support_agent_presence"

    live_columns = set(SupportLiveSession.__table__.columns.keys())
    assert {
        "session_code",
        "conversation_id",
        "customer_id",
        "anonymous_id",
        "visitor_session_code",
        "assigned_agent_id",
        "status",
        "source",
        "session_token_hash",
        "started_at",
        "accepted_at",
        "ended_at",
        "last_customer_seen_at",
        "last_agent_seen_at",
        "last_message_at",
    }.issubset(live_columns)

    presence_columns = set(SupportAgentPresence.__table__.columns.keys())
    assert {
        "agent_id",
        "agent_code",
        "presence_status",
        "max_active_sessions",
        "active_session_count",
        "last_heartbeat_at",
    }.issubset(presence_columns)


def test_support_live_tables_exist_in_database() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_support_live_sessions" in table_names
        assert "d2c_support_agent_presence" in table_names

        live_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_live_sessions")
        }
        assert {
            "session_code",
            "conversation_id",
            "status",
            "session_token_hash",
            "started_at",
            "accepted_at",
            "ended_at",
        }.issubset(live_columns)

        presence_columns = {
            column["name"] for column in inspector.get_columns("d2c_support_agent_presence")
        }
        assert {
            "agent_id",
            "agent_code",
            "presence_status",
            "max_active_sessions",
            "active_session_count",
            "last_heartbeat_at",
        }.issubset(presence_columns)

        live_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_support_live_sessions")
        }
        assert "d2c_support_conversations" in live_fk_targets
        assert "d2c_support_agent_profiles" in live_fk_targets

        presence_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_support_agent_presence")
        }
        assert presence_fk_targets == {"d2c_support_agent_profiles"}
    finally:
        engine.dispose()


def test_support_live_migration_contains_live_model() -> None:
    text = Path("alembic/versions/0040_support_live.py").read_text(encoding="utf-8")

    for token in (
        "d2c_support_live_sessions",
        "d2c_support_agent_presence",
        "waiting",
        "active",
        "ended",
        "missed",
        "online",
        "away",
        "offline",
        "storefront_widget",
        "session_token_hash",
    ):
        assert token in text
