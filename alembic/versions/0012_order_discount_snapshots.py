"""add_order_discount_snapshots.

Revision ID: 0012_order_discount_snapshots
Revises: 0011_promotion_coupon_tables
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_order_discount_snapshots"
down_revision: str | Sequence[str] | None = "0011_promotion_coupon_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "d2c_orders",
        sa.Column(
            "discount_cents",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "d2c_orders",
        sa.Column(
            "payable_cents",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "d2c_orders",
        sa.Column(
            "promotion_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.add_column(
        "d2c_orders",
        sa.Column(
            "promotion_code",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE d2c_orders
        SET payable_cents = subtotal_cents - discount_cents
        WHERE payable_cents IS NULL
        """
    )

    op.alter_column(
        "d2c_orders",
        "payable_cents",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_check_constraint(
        "ck_d2c_orders_discount_cents_non_negative",
        "d2c_orders",
        "discount_cents >= 0",
    )
    op.create_check_constraint(
        "ck_d2c_orders_payable_cents_non_negative",
        "d2c_orders",
        "payable_cents >= 0",
    )
    op.create_check_constraint(
        "ck_d2c_orders_discount_not_exceed_subtotal",
        "d2c_orders",
        "discount_cents <= subtotal_cents",
    )
    op.create_check_constraint(
        "ck_d2c_orders_payable_matches_discount",
        "d2c_orders",
        "payable_cents = subtotal_cents - discount_cents",
    )
    op.create_foreign_key(
        "fk_d2c_orders_promotion_id",
        "d2c_orders",
        "d2c_promotions",
        ["promotion_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_d2c_orders_promotion_id",
        "d2c_orders",
        ["promotion_id"],
    )
    op.create_index(
        "ix_d2c_orders_promotion_code",
        "d2c_orders",
        ["promotion_code"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_d2c_orders_promotion_code", table_name="d2c_orders")
    op.drop_index("ix_d2c_orders_promotion_id", table_name="d2c_orders")
    op.drop_constraint(
        "fk_d2c_orders_promotion_id",
        "d2c_orders",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_d2c_orders_payable_matches_discount",
        "d2c_orders",
        type_="check",
    )
    op.drop_constraint(
        "ck_d2c_orders_discount_not_exceed_subtotal",
        "d2c_orders",
        type_="check",
    )
    op.drop_constraint(
        "ck_d2c_orders_payable_cents_non_negative",
        "d2c_orders",
        type_="check",
    )
    op.drop_constraint(
        "ck_d2c_orders_discount_cents_non_negative",
        "d2c_orders",
        type_="check",
    )
    op.drop_column("d2c_orders", "promotion_code")
    op.drop_column("d2c_orders", "promotion_id")
    op.drop_column("d2c_orders", "payable_cents")
    op.drop_column("d2c_orders", "discount_cents")
