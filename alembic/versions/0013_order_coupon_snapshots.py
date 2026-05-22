"""add_order_coupon_snapshots.

Revision ID: 0013_order_coupon_snapshots
Revises: 0012_order_discount_snapshots
Create Date: 2026-05-23

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013_order_coupon_snapshots"
down_revision: str | Sequence[str] | None = "0012_order_discount_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "d2c_orders",
        sa.Column("coupon_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_orders",
        sa.Column("coupon_code", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_d2c_orders_coupon_id",
        "d2c_orders",
        "d2c_coupons",
        ["coupon_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_d2c_orders_coupon_id",
        "d2c_orders",
        ["coupon_id"],
    )
    op.create_index(
        "ix_d2c_orders_coupon_code",
        "d2c_orders",
        ["coupon_code"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_d2c_orders_coupon_code", table_name="d2c_orders")
    op.drop_index("ix_d2c_orders_coupon_id", table_name="d2c_orders")
    op.drop_constraint(
        "fk_d2c_orders_coupon_id",
        "d2c_orders",
        type_="foreignkey",
    )
    op.drop_column("d2c_orders", "coupon_code")
    op.drop_column("d2c_orders", "coupon_id")
