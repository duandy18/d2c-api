"""cart owner tables

Revision ID: 0005_cart_owner_tables
Revises: 0004_analytics_behavior_events
Create Date: 2026-05-22

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_cart_owner_tables"
down_revision: str | Sequence[str] | None = "0004_analytics_behavior_events"
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
        "d2c_carts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("cart_code", sa.String(length=96), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("anonymous_id", sa.String(length=96), nullable=True),
        sa.Column("session_code", sa.String(length=96), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_carts_customer_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("cart_code", name="uq_d2c_carts_cart_code"),
    )
    op.create_index("ix_d2c_carts_anonymous_id", "d2c_carts", ["anonymous_id"])
    op.create_index("ix_d2c_carts_cart_code", "d2c_carts", ["cart_code"])
    op.create_index("ix_d2c_carts_customer_id", "d2c_carts", ["customer_id"])
    op.create_index("ix_d2c_carts_session_code", "d2c_carts", ["session_code"])
    op.create_index("ix_d2c_carts_status", "d2c_carts", ["status"])

    op.create_table(
        "d2c_cart_lines",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("cart_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("line_subtotal_cents", sa.Integer(), nullable=False),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["d2c_carts.id"],
            name="fk_d2c_cart_lines_cart_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["d2c_products.id"],
            name="fk_d2c_cart_lines_product_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["d2c_product_skus.id"],
            name="fk_d2c_cart_lines_sku_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("cart_id", "sku_id", name="uq_d2c_cart_lines_cart_id_sku_id"),
    )
    op.create_index("ix_d2c_cart_lines_cart_id", "d2c_cart_lines", ["cart_id"])
    op.create_index("ix_d2c_cart_lines_product_id", "d2c_cart_lines", ["product_id"])
    op.create_index("ix_d2c_cart_lines_sku_id", "d2c_cart_lines", ["sku_id"])


def downgrade() -> None:
    op.drop_index("ix_d2c_cart_lines_sku_id", table_name="d2c_cart_lines")
    op.drop_index("ix_d2c_cart_lines_product_id", table_name="d2c_cart_lines")
    op.drop_index("ix_d2c_cart_lines_cart_id", table_name="d2c_cart_lines")
    op.drop_table("d2c_cart_lines")

    op.drop_index("ix_d2c_carts_status", table_name="d2c_carts")
    op.drop_index("ix_d2c_carts_session_code", table_name="d2c_carts")
    op.drop_index("ix_d2c_carts_customer_id", table_name="d2c_carts")
    op.drop_index("ix_d2c_carts_cart_code", table_name="d2c_carts")
    op.drop_index("ix_d2c_carts_anonymous_id", table_name="d2c_carts")
    op.drop_table("d2c_carts")
