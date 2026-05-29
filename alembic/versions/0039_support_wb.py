"""Add support workbench owner model.

Revision ID: 0039_support_wb
Revises: 0038_support
Create Date: 2026-05-29
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0039_support_wb"
down_revision = "0038_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "d2c_support_contacts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("contact_code", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("anonymous_id", sa.String(length=96), nullable=True),
        sa.Column("contact_name", sa.String(length=120), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="storefront"),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_support_contact_customer",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("contact_code", name="uq_d2c_support_contact_code"),
        sa.UniqueConstraint("customer_id", name="uq_d2c_support_contact_customer"),
    )
    op.create_index("ix_d2c_support_contact_customer", "d2c_support_contacts", ["customer_id"])
    op.create_index("ix_d2c_support_contact_email", "d2c_support_contacts", ["contact_email"])
    op.create_index("ix_d2c_support_contact_phone", "d2c_support_contacts", ["contact_phone"])
    op.create_index("ix_d2c_support_contact_anon", "d2c_support_contacts", ["anonymous_id"])

    op.create_table(
        "d2c_support_agent_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("agent_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("agent_code", name="uq_d2c_support_agent_code"),
        sa.UniqueConstraint("email", name="uq_d2c_support_agent_email"),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_d2c_support_agent_status"),
    )
    op.create_index("ix_d2c_support_agent_status", "d2c_support_agent_profiles", ["status"])
    op.create_index("ix_d2c_support_agent_email", "d2c_support_agent_profiles", ["email"])

    op.add_column(
        "d2c_support_conversations",
        sa.Column("contact_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_support_conversations",
        sa.Column("assigned_agent_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_support_conversations",
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"),
    )
    op.add_column(
        "d2c_support_conversations",
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "d2c_support_conversations",
        sa.Column("last_customer_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "d2c_support_conversations",
        sa.Column("last_agent_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "d2c_support_conversations",
        sa.Column("last_system_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_d2c_support_conv_contact",
        "d2c_support_conversations",
        "d2c_support_contacts",
        ["contact_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_d2c_support_conv_agent",
        "d2c_support_conversations",
        "d2c_support_agent_profiles",
        ["assigned_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_d2c_support_conv_contact", "d2c_support_conversations", ["contact_id"])
    op.create_index("ix_d2c_support_conv_agent", "d2c_support_conversations", ["assigned_agent_id"])
    op.create_index(
        "ix_d2c_support_conv_last_msg", "d2c_support_conversations", ["last_message_at"]
    )
    op.drop_constraint(
        "ck_d2c_support_conv_status",
        "d2c_support_conversations",
        type_="check",
    )
    op.create_check_constraint(
        "ck_d2c_support_conv_status",
        "d2c_support_conversations",
        "status IN ('open', 'pending_agent', 'pending_customer', 'closed')",
    )
    op.create_check_constraint(
        "ck_d2c_support_conv_priority",
        "d2c_support_conversations",
        "priority IN ('low', 'normal', 'high')",
    )
    op.execute(
        """
        UPDATE d2c_support_conversations
        SET status = CASE WHEN status = 'open' THEN 'pending_agent' ELSE status END,
            last_message_at = COALESCE(last_message_at, updated_at),
            last_customer_message_at = COALESCE(last_customer_message_at, updated_at),
            last_system_message_at = COALESCE(last_system_message_at, updated_at)
        """
    )

    op.add_column(
        "d2c_support_messages",
        sa.Column("agent_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_support_messages",
        sa.Column("message_kind", sa.String(length=32), nullable=False, server_default="text"),
    )
    op.create_foreign_key(
        "fk_d2c_support_msg_agent",
        "d2c_support_messages",
        "d2c_support_agent_profiles",
        ["agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_d2c_support_msg_agent", "d2c_support_messages", ["agent_id"])
    op.drop_constraint(
        "ck_d2c_support_msg_visibility",
        "d2c_support_messages",
        type_="check",
    )
    op.create_check_constraint(
        "ck_d2c_support_msg_visibility",
        "d2c_support_messages",
        "visibility IN ('public', 'internal')",
    )
    op.create_check_constraint(
        "ck_d2c_support_msg_kind",
        "d2c_support_messages",
        "message_kind IN ('text', 'note')",
    )

    op.create_table(
        "d2c_support_conversation_assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("assignment_code", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_by_agent_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["d2c_support_conversations.id"],
            name="fk_d2c_support_assign_conv",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["d2c_support_agent_profiles.id"],
            name="fk_d2c_support_assign_agent",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_agent_id"],
            ["d2c_support_agent_profiles.id"],
            name="fk_d2c_support_assign_by_agent",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("assignment_code", name="uq_d2c_support_assign_code"),
        sa.CheckConstraint("status IN ('active', 'replaced')", name="ck_d2c_support_assign_status"),
    )
    op.create_index(
        "ix_d2c_support_assign_conv", "d2c_support_conversation_assignments", ["conversation_id"]
    )
    op.create_index(
        "ix_d2c_support_assign_agent", "d2c_support_conversation_assignments", ["agent_id"]
    )
    op.create_index(
        "ix_d2c_support_assign_status", "d2c_support_conversation_assignments", ["status"]
    )

    op.create_table(
        "d2c_support_conversation_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_code", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_agent_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("assignment_id", sa.BigInteger(), nullable=True),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["d2c_support_conversations.id"],
            name="fk_d2c_support_event_conv",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_agent_id"],
            ["d2c_support_agent_profiles.id"],
            name="fk_d2c_support_event_agent",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["d2c_support_messages.id"],
            name="fk_d2c_support_event_msg",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["d2c_support_conversation_assignments.id"],
            name="fk_d2c_support_event_assign",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("event_code", name="uq_d2c_support_event_code"),
        sa.CheckConstraint(
            "actor_type IN ('customer', 'agent', 'system')",
            name="ck_d2c_support_event_actor",
        ),
    )
    op.create_index(
        "ix_d2c_support_event_conv", "d2c_support_conversation_events", ["conversation_id"]
    )
    op.create_index("ix_d2c_support_event_type", "d2c_support_conversation_events", ["event_type"])
    op.create_index(
        "ix_d2c_support_event_agent", "d2c_support_conversation_events", ["actor_agent_id"]
    )
    op.create_index(
        "ix_d2c_support_event_created", "d2c_support_conversation_events", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_support_event_created", table_name="d2c_support_conversation_events")
    op.drop_index("ix_d2c_support_event_agent", table_name="d2c_support_conversation_events")
    op.drop_index("ix_d2c_support_event_type", table_name="d2c_support_conversation_events")
    op.drop_index("ix_d2c_support_event_conv", table_name="d2c_support_conversation_events")
    op.drop_table("d2c_support_conversation_events")

    op.drop_index("ix_d2c_support_assign_status", table_name="d2c_support_conversation_assignments")
    op.drop_index("ix_d2c_support_assign_agent", table_name="d2c_support_conversation_assignments")
    op.drop_index("ix_d2c_support_assign_conv", table_name="d2c_support_conversation_assignments")
    op.drop_table("d2c_support_conversation_assignments")

    op.drop_constraint("ck_d2c_support_msg_kind", "d2c_support_messages", type_="check")
    op.drop_constraint("ck_d2c_support_msg_visibility", "d2c_support_messages", type_="check")
    op.create_check_constraint(
        "ck_d2c_support_msg_visibility",
        "d2c_support_messages",
        "visibility IN ('public')",
    )
    op.drop_index("ix_d2c_support_msg_agent", table_name="d2c_support_messages")
    op.drop_constraint("fk_d2c_support_msg_agent", "d2c_support_messages", type_="foreignkey")
    op.drop_column("d2c_support_messages", "message_kind")
    op.drop_column("d2c_support_messages", "agent_id")

    op.drop_constraint("ck_d2c_support_conv_priority", "d2c_support_conversations", type_="check")
    op.drop_constraint("ck_d2c_support_conv_status", "d2c_support_conversations", type_="check")
    op.execute(
        """
        UPDATE d2c_support_conversations
        SET status = CASE
            WHEN status IN ('pending_agent', 'pending_customer') THEN 'open'
            ELSE status
        END
        """
    )
    op.create_check_constraint(
        "ck_d2c_support_conv_status",
        "d2c_support_conversations",
        "status IN ('open', 'closed')",
    )
    op.drop_index("ix_d2c_support_conv_last_msg", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_agent", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_contact", table_name="d2c_support_conversations")
    op.drop_constraint("fk_d2c_support_conv_agent", "d2c_support_conversations", type_="foreignkey")
    op.drop_constraint(
        "fk_d2c_support_conv_contact", "d2c_support_conversations", type_="foreignkey"
    )
    op.drop_column("d2c_support_conversations", "last_system_message_at")
    op.drop_column("d2c_support_conversations", "last_agent_message_at")
    op.drop_column("d2c_support_conversations", "last_customer_message_at")
    op.drop_column("d2c_support_conversations", "last_message_at")
    op.drop_column("d2c_support_conversations", "priority")
    op.drop_column("d2c_support_conversations", "assigned_agent_id")
    op.drop_column("d2c_support_conversations", "contact_id")

    op.drop_index("ix_d2c_support_agent_email", table_name="d2c_support_agent_profiles")
    op.drop_index("ix_d2c_support_agent_status", table_name="d2c_support_agent_profiles")
    op.drop_table("d2c_support_agent_profiles")

    op.drop_index("ix_d2c_support_contact_anon", table_name="d2c_support_contacts")
    op.drop_index("ix_d2c_support_contact_phone", table_name="d2c_support_contacts")
    op.drop_index("ix_d2c_support_contact_email", table_name="d2c_support_contacts")
    op.drop_index("ix_d2c_support_contact_customer", table_name="d2c_support_contacts")
    op.drop_table("d2c_support_contacts")
