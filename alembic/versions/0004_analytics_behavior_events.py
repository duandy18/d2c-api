"""analytics behavior events

Revision ID: 0004_analytics_behavior_events
Revises: 0003_customer_account_tables
Create Date: 2026-05-22

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_analytics_behavior_events"
down_revision: str | Sequence[str] | None = "0003_customer_account_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    op.create_table(
        "d2c_visitor_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("session_code", sa.String(length=96), nullable=False),
        sa.Column("anonymous_id", sa.String(length=96), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        timestamp_column("started_at"),
        timestamp_column("last_seen_at"),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("utm_source", sa.String(length=120), nullable=True),
        sa.Column("utm_medium", sa.String(length=120), nullable=True),
        sa.Column("utm_campaign", sa.String(length=120), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_visitor_sessions_customer_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("session_code", name="uq_d2c_visitor_sessions_session_code"),
    )
    op.create_index(
        "ix_d2c_visitor_sessions_anonymous_id",
        "d2c_visitor_sessions",
        ["anonymous_id"],
    )
    op.create_index(
        "ix_d2c_visitor_sessions_customer_id",
        "d2c_visitor_sessions",
        ["customer_id"],
    )
    op.create_index(
        "ix_d2c_visitor_sessions_session_code",
        "d2c_visitor_sessions",
        ["session_code"],
    )

    op.create_table(
        "d2c_behavior_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_code", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("anonymous_id", sa.String(length=96), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("page_path", sa.Text(), nullable=False),
        sa.Column("product_code", sa.String(length=96), nullable=True),
        sa.Column("sku_code", sa.String(length=96), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        timestamp_column("created_at"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_behavior_events_customer_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["d2c_visitor_sessions.id"],
            name="fk_d2c_behavior_events_session_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("event_code", name="uq_d2c_behavior_events_event_code"),
    )
    op.create_index(
        "ix_d2c_behavior_events_anonymous_id",
        "d2c_behavior_events",
        ["anonymous_id"],
    )
    op.create_index(
        "ix_d2c_behavior_events_customer_id",
        "d2c_behavior_events",
        ["customer_id"],
    )
    op.create_index(
        "ix_d2c_behavior_events_event_type",
        "d2c_behavior_events",
        ["event_type"],
    )
    op.create_index(
        "ix_d2c_behavior_events_occurred_at",
        "d2c_behavior_events",
        ["occurred_at"],
    )
    op.create_index(
        "ix_d2c_behavior_events_product_code",
        "d2c_behavior_events",
        ["product_code"],
    )
    op.create_index(
        "ix_d2c_behavior_events_session_id",
        "d2c_behavior_events",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_behavior_events_session_id", table_name="d2c_behavior_events")
    op.drop_index("ix_d2c_behavior_events_product_code", table_name="d2c_behavior_events")
    op.drop_index("ix_d2c_behavior_events_occurred_at", table_name="d2c_behavior_events")
    op.drop_index("ix_d2c_behavior_events_event_type", table_name="d2c_behavior_events")
    op.drop_index("ix_d2c_behavior_events_customer_id", table_name="d2c_behavior_events")
    op.drop_index("ix_d2c_behavior_events_anonymous_id", table_name="d2c_behavior_events")
    op.drop_table("d2c_behavior_events")

    op.drop_index("ix_d2c_visitor_sessions_session_code", table_name="d2c_visitor_sessions")
    op.drop_index("ix_d2c_visitor_sessions_customer_id", table_name="d2c_visitor_sessions")
    op.drop_index("ix_d2c_visitor_sessions_anonymous_id", table_name="d2c_visitor_sessions")
    op.drop_table("d2c_visitor_sessions")
