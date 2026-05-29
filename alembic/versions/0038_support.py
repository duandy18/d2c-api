"""Add storefront support conversations.

Revision ID: 0038_support
Revises: 0037_my_single
Create Date: 2026-05-29
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0038_support"
down_revision = "0037_my_single"
branch_labels = None
depends_on = None


SUPPORT_PAGE = {
    "page_code": "customer_service",
    "page_type": "customer_service",
    "route_path": "/support",
    "title": "客户服务",
    "description": "顾客咨询与客服聊天",
    "seo_title": "客户服务",
    "seo_description": "顾客咨询与客服聊天",
    "auth_required": False,
    "navigation_label": "客户服务",
    "navigation_group": "support",
    "sort_order": 80,
}


def upgrade() -> None:
    op.create_table(
        "d2c_support_conversations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("conversation_code", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("anonymous_id", sa.String(length=96), nullable=True),
        sa.Column("session_code", sa.String(length=96), nullable=True),
        sa.Column("contact_name", sa.String(length=120), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column("related_order_no", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="storefront"),
        sa.Column("conversation_token_hash", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_support_conv_customer",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("conversation_code", name="uq_d2c_support_conv_code"),
        sa.UniqueConstraint("conversation_token_hash", name="uq_d2c_support_conv_token_hash"),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_d2c_support_conv_status"),
        sa.CheckConstraint("source IN ('storefront')", name="ck_d2c_support_conv_source"),
    )
    op.create_index("ix_d2c_support_conv_customer", "d2c_support_conversations", ["customer_id"])
    op.create_index("ix_d2c_support_conv_anon", "d2c_support_conversations", ["anonymous_id"])
    op.create_index("ix_d2c_support_conv_status", "d2c_support_conversations", ["status"])
    op.create_index("ix_d2c_support_conv_topic", "d2c_support_conversations", ["topic"])
    op.create_index("ix_d2c_support_conv_order", "d2c_support_conversations", ["related_order_no"])
    op.create_index("ix_d2c_support_conv_created", "d2c_support_conversations", ["created_at"])

    op.create_table(
        "d2c_support_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("message_code", sa.String(length=64), nullable=False),
        sa.Column("sender_type", sa.String(length=32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="public"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["d2c_support_conversations.id"],
            name="fk_d2c_support_msg_conv",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("message_code", name="uq_d2c_support_msg_code"),
        sa.CheckConstraint(
            "sender_type IN ('customer', 'agent', 'system')",
            name="ck_d2c_support_msg_sender",
        ),
        sa.CheckConstraint("visibility IN ('public')", name="ck_d2c_support_msg_visibility"),
    )
    op.create_index("ix_d2c_support_msg_conv", "d2c_support_messages", ["conversation_id"])
    op.create_index("ix_d2c_support_msg_created", "d2c_support_messages", ["created_at"])

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO d2c_storefront_pages (
              site_id,
              page_code,
              page_type,
              route_path,
              title,
              description,
              status,
              seo_title,
              seo_description,
              auth_required,
              navigation_label,
              navigation_group,
              sort_order
            )
            SELECT
              id,
              :page_code,
              :page_type,
              :route_path,
              :title,
              :description,
              'active',
              :seo_title,
              :seo_description,
              :auth_required,
              :navigation_label,
              :navigation_group,
              :sort_order
            FROM d2c_storefront_sites
            WHERE site_code = 'default'
            ON CONFLICT (site_id, page_code) DO UPDATE SET
              page_type = EXCLUDED.page_type,
              route_path = EXCLUDED.route_path,
              title = EXCLUDED.title,
              description = EXCLUDED.description,
              status = EXCLUDED.status,
              seo_title = EXCLUDED.seo_title,
              seo_description = EXCLUDED.seo_description,
              auth_required = EXCLUDED.auth_required,
              navigation_label = EXCLUDED.navigation_label,
              navigation_group = EXCLUDED.navigation_group,
              sort_order = EXCLUDED.sort_order,
              updated_at = now()
            """
        ),
        SUPPORT_PAGE,
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code = 'customer_service'
        """
    )

    op.drop_index("ix_d2c_support_msg_created", table_name="d2c_support_messages")
    op.drop_index("ix_d2c_support_msg_conv", table_name="d2c_support_messages")
    op.drop_table("d2c_support_messages")

    op.drop_index("ix_d2c_support_conv_created", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_order", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_topic", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_status", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_anon", table_name="d2c_support_conversations")
    op.drop_index("ix_d2c_support_conv_customer", table_name="d2c_support_conversations")
    op.drop_table("d2c_support_conversations")
