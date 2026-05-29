"""Add support live sessions.

Revision ID: 0040_support_live
Revises: 0039_support_wb
Create Date: 2026-05-29
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0040_support_live"
down_revision = "0039_support_wb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "d2c_support_agent_presence",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_code", sa.String(length=64), nullable=False),
        sa.Column(
            "presence_status", sa.String(length=32), nullable=False, server_default="offline"
        ),
        sa.Column("max_active_sessions", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("active_session_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["d2c_support_agent_profiles.id"],
            name="fk_d2c_supp_pres_agent",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("agent_id", name="uq_d2c_supp_pres_agent"),
        sa.UniqueConstraint("agent_code", name="uq_d2c_supp_pres_code"),
        sa.CheckConstraint(
            "presence_status IN ('online', 'away', 'offline')",
            name="ck_d2c_supp_pres_status",
        ),
        sa.CheckConstraint(
            "max_active_sessions >= 1 AND active_session_count >= 0",
            name="ck_d2c_supp_pres_counts",
        ),
    )
    op.create_index("ix_d2c_supp_pres_status", "d2c_support_agent_presence", ["presence_status"])
    op.create_index(
        "ix_d2c_supp_pres_heartbeat",
        "d2c_support_agent_presence",
        ["last_heartbeat_at"],
    )

    op.create_table(
        "d2c_support_live_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("session_code", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("anonymous_id", sa.String(length=96), nullable=True),
        sa.Column("visitor_session_code", sa.String(length=96), nullable=True),
        sa.Column("assigned_agent_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="waiting"),
        sa.Column(
            "source", sa.String(length=32), nullable=False, server_default="storefront_widget"
        ),
        sa.Column("session_token_hash", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_customer_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_agent_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["d2c_support_conversations.id"],
            name="fk_d2c_supp_live_conv",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_supp_live_customer",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"],
            ["d2c_support_agent_profiles.id"],
            name="fk_d2c_supp_live_agent",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("session_code", name="uq_d2c_supp_live_sess_code"),
        sa.UniqueConstraint("session_token_hash", name="uq_d2c_supp_live_sess_hash"),
        sa.CheckConstraint(
            "status IN ('waiting', 'active', 'ended', 'missed')",
            name="ck_d2c_supp_live_status",
        ),
        sa.CheckConstraint(
            "source IN ('storefront_widget')",
            name="ck_d2c_supp_live_source",
        ),
    )
    op.create_index("ix_d2c_supp_live_conv", "d2c_support_live_sessions", ["conversation_id"])
    op.create_index("ix_d2c_supp_live_customer", "d2c_support_live_sessions", ["customer_id"])
    op.create_index("ix_d2c_supp_live_agent", "d2c_support_live_sessions", ["assigned_agent_id"])
    op.create_index("ix_d2c_supp_live_anon", "d2c_support_live_sessions", ["anonymous_id"])
    op.create_index("ix_d2c_supp_live_status", "d2c_support_live_sessions", ["status"])
    op.create_index("ix_d2c_supp_live_started", "d2c_support_live_sessions", ["started_at"])
    op.create_index("ix_d2c_supp_live_last_msg", "d2c_support_live_sessions", ["last_message_at"])


def downgrade() -> None:
    op.drop_index("ix_d2c_supp_live_last_msg", table_name="d2c_support_live_sessions")
    op.drop_index("ix_d2c_supp_live_started", table_name="d2c_support_live_sessions")
    op.drop_index("ix_d2c_supp_live_status", table_name="d2c_support_live_sessions")
    op.drop_index("ix_d2c_supp_live_anon", table_name="d2c_support_live_sessions")
    op.drop_index("ix_d2c_supp_live_agent", table_name="d2c_support_live_sessions")
    op.drop_index("ix_d2c_supp_live_customer", table_name="d2c_support_live_sessions")
    op.drop_index("ix_d2c_supp_live_conv", table_name="d2c_support_live_sessions")
    op.drop_table("d2c_support_live_sessions")

    op.drop_index("ix_d2c_supp_pres_heartbeat", table_name="d2c_support_agent_presence")
    op.drop_index("ix_d2c_supp_pres_status", table_name="d2c_support_agent_presence")
    op.drop_table("d2c_support_agent_presence")
