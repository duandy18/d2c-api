"""strengthen cart and order item snapshots.

Revision ID: 0018_snap
Revises: 0017_cart_pub
Create Date: 2026-05-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018_snap"
down_revision: str | Sequence[str] | None = "0017_cart_pub"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ITEM_SNAPSHOT_COLUMNS = [
    sa.Column("pms_item_id", sa.BigInteger(), nullable=True),
    sa.Column("pms_sku", sa.String(length=128), nullable=True),
    sa.Column("category_code", sa.String(length=96), nullable=True),
    sa.Column("category_name", sa.String(length=160), nullable=True),
    sa.Column("brand_code", sa.String(length=96), nullable=True),
    sa.Column("brand_name", sa.String(length=160), nullable=True),
    sa.Column("sales_unit_code", sa.String(length=64), nullable=True),
    sa.Column("sales_unit_name", sa.String(length=120), nullable=True),
    sa.Column("barcode", sa.String(length=128), nullable=True),
    sa.Column("spec_text", sa.String(length=240), nullable=True),
    sa.Column("price_list_code", sa.String(length=96), nullable=True),
    sa.Column("compare_at_price_cents", sa.Integer(), nullable=True),
    sa.Column("source_product_id", sa.BigInteger(), nullable=True),
    sa.Column("source_sku_id", sa.BigInteger(), nullable=True),
    sa.Column("source_price_id", sa.BigInteger(), nullable=True),
]


ORDER_SNAPSHOT_COLUMNS = [
    sa.Column("promotion_name", sa.String(length=160), nullable=True),
    sa.Column("promotion_type", sa.String(length=32), nullable=True),
    sa.Column("promotion_discount_type", sa.String(length=32), nullable=True),
    sa.Column("promotion_discount_value", sa.Integer(), nullable=True),
    sa.Column("promotion_publish_version", sa.String(length=64), nullable=True),
    sa.Column("coupon_name", sa.String(length=160), nullable=True),
    sa.Column("coupon_type", sa.String(length=32), nullable=True),
    sa.Column("coupon_publish_version", sa.String(length=64), nullable=True),
]


def _add_item_snapshot_columns(table_name: str) -> None:
    for column in ITEM_SNAPSHOT_COLUMNS:
        op.add_column(table_name, column.copy())


def _drop_item_snapshot_columns(table_name: str) -> None:
    for column in reversed(ITEM_SNAPSHOT_COLUMNS):
        op.drop_column(table_name, column.name)


def upgrade() -> None:
    _add_item_snapshot_columns("d2c_cart_lines")
    _add_item_snapshot_columns("d2c_order_lines")

    for column in ORDER_SNAPSHOT_COLUMNS:
        op.add_column("d2c_orders", column.copy())

    op.create_index(
        "ix_d2c_order_lines_category_code",
        "d2c_order_lines",
        ["category_code"],
    )
    op.create_index(
        "ix_d2c_order_lines_brand_code",
        "d2c_order_lines",
        ["brand_code"],
    )
    op.create_index(
        "ix_d2c_order_lines_price_list_code",
        "d2c_order_lines",
        ["price_list_code"],
    )
    op.create_index(
        "ix_d2c_orders_promotion_publish_version",
        "d2c_orders",
        ["promotion_publish_version"],
    )
    op.create_index(
        "ix_d2c_orders_coupon_publish_version",
        "d2c_orders",
        ["coupon_publish_version"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_orders_coupon_publish_version", table_name="d2c_orders")
    op.drop_index("ix_d2c_orders_promotion_publish_version", table_name="d2c_orders")
    op.drop_index("ix_d2c_order_lines_price_list_code", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_brand_code", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_category_code", table_name="d2c_order_lines")

    for column in reversed(ORDER_SNAPSHOT_COLUMNS):
        op.drop_column("d2c_orders", column.name)

    _drop_item_snapshot_columns("d2c_order_lines")
    _drop_item_snapshot_columns("d2c_cart_lines")
