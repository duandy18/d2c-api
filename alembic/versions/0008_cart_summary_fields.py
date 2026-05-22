"""add_cart_summary_fields.

Revision ID: 0008_cart_summary_fields
Revises: 0007_d2c_order_owner_tables
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_cart_summary_fields"
down_revision: str | Sequence[str] | None = "0007_d2c_order_owner_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "d2c_carts",
        sa.Column(
            "line_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "d2c_carts",
        sa.Column(
            "item_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "d2c_carts",
        sa.Column(
            "subtotal_cents",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )

    op.execute(
        """
        UPDATE d2c_carts c
        SET
          line_count = COALESCE(s.line_count, 0),
          item_count = COALESCE(s.item_count, 0),
          subtotal_cents = COALESCE(s.subtotal_cents, 0)
        FROM (
          SELECT
            cart_id,
            COUNT(*)::integer AS line_count,
            COALESCE(SUM(quantity), 0)::integer AS item_count,
            COALESCE(SUM(line_subtotal_cents), 0)::integer AS subtotal_cents
          FROM d2c_cart_lines
          GROUP BY cart_id
        ) s
        WHERE s.cart_id = c.id
        """
    )

    op.create_check_constraint(
        "ck_d2c_carts_line_count_non_negative",
        "d2c_carts",
        "line_count >= 0",
    )
    op.create_check_constraint(
        "ck_d2c_carts_item_count_non_negative",
        "d2c_carts",
        "item_count >= 0",
    )
    op.create_check_constraint(
        "ck_d2c_carts_subtotal_cents_non_negative",
        "d2c_carts",
        "subtotal_cents >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_d2c_carts_subtotal_cents_non_negative",
        "d2c_carts",
        type_="check",
    )
    op.drop_constraint(
        "ck_d2c_carts_item_count_non_negative",
        "d2c_carts",
        type_="check",
    )
    op.drop_constraint(
        "ck_d2c_carts_line_count_non_negative",
        "d2c_carts",
        type_="check",
    )
    op.drop_column("d2c_carts", "subtotal_cents")
    op.drop_column("d2c_carts", "item_count")
    op.drop_column("d2c_carts", "line_count")
