"""add_order_owner_tables.

Revision ID: 0007_d2c_order_owner_tables
Revises: 0005_cart_owner_tables
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_d2c_order_owner_tables"
down_revision: str | Sequence[str] | None = "0005_cart_owner_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "d2c_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("recipient_name", sa.String(length=128), nullable=False),
        sa.Column("recipient_phone", sa.String(length=32), nullable=False),
        sa.Column("shipping_country", sa.String(length=64), nullable=False),
        sa.Column("shipping_province", sa.String(length=64), nullable=False),
        sa.Column("shipping_city", sa.String(length=64), nullable=False),
        sa.Column("shipping_district", sa.String(length=64), nullable=True),
        sa.Column("shipping_address_line1", sa.String(length=255), nullable=False),
        sa.Column("shipping_address_line2", sa.String(length=255), nullable=True),
        sa.Column("shipping_postal_code", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "item_count >= 0",
            name="ck_d2c_orders_item_count_non_negative",
        ),
        sa.CheckConstraint(
            "subtotal_cents >= 0",
            name="ck_d2c_orders_subtotal_cents_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["d2c_carts.id"],
            name="fk_d2c_orders_cart_id",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_orders_customer_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_id", name="uq_d2c_orders_cart_id"),
        sa.UniqueConstraint("order_no", name="uq_d2c_orders_order_no"),
    )
    op.create_index(
        "ix_d2c_orders_customer_id",
        "d2c_orders",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_orders_status",
        "d2c_orders",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_orders_created_at",
        "d2c_orders",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "d2c_order_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("sku_id", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(length=64), nullable=False),
        sa.Column("sku_code", sa.String(length=64), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("sku_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("line_subtotal_cents", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_d2c_order_lines_quantity_positive",
        ),
        sa.CheckConstraint(
            "unit_price_cents >= 0",
            name="ck_d2c_order_lines_unit_price_cents_non_negative",
        ),
        sa.CheckConstraint(
            "line_subtotal_cents >= 0",
            name="ck_d2c_order_lines_line_subtotal_cents_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["d2c_orders.id"],
            name="fk_d2c_order_lines_order_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["d2c_products.id"],
            name="fk_d2c_order_lines_product_id",
        ),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["d2c_product_skus.id"],
            name="fk_d2c_order_lines_sku_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_d2c_order_lines_order_id",
        "d2c_order_lines",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_order_lines_product_id",
        "d2c_order_lines",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_order_lines_sku_id",
        "d2c_order_lines",
        ["sku_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_d2c_order_lines_sku_id", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_product_id", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_order_id", table_name="d2c_order_lines")
    op.drop_table("d2c_order_lines")

    op.drop_index("ix_d2c_orders_created_at", table_name="d2c_orders")
    op.drop_index("ix_d2c_orders_status", table_name="d2c_orders")
    op.drop_index("ix_d2c_orders_customer_id", table_name="d2c_orders")
    op.drop_table("d2c_orders")
