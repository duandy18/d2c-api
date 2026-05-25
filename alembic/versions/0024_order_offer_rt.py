"""add_order_line_offer_snapshot_fields.

Revision ID: 0024_order_offer_rt
Revises: 0023_cart_offer_rt
Create Date: 2026-05-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0024_order_offer_rt"
down_revision: str | Sequence[str] | None = "0023_cart_offer_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("d2c_order_lines", sa.Column("offer_code", sa.String(length=96), nullable=True))
    op.add_column("d2c_order_lines", sa.Column("offer_title", sa.String(length=200), nullable=True))
    op.add_column("d2c_order_lines", sa.Column("offer_type", sa.String(length=32), nullable=True))
    op.add_column(
        "d2c_order_lines", sa.Column("offer_subtitle", sa.String(length=240), nullable=True)
    )
    op.add_column("d2c_order_lines", sa.Column("offer_image_url", sa.Text(), nullable=True))
    op.add_column("d2c_order_lines", sa.Column("group_code", sa.String(length=96), nullable=True))
    op.add_column("d2c_order_lines", sa.Column("group_name", sa.String(length=160), nullable=True))
    op.add_column("d2c_order_lines", sa.Column("price_code", sa.String(length=96), nullable=True))
    op.add_column("d2c_order_lines", sa.Column("source_offer_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "d2c_order_lines", sa.Column("source_position_id", sa.BigInteger(), nullable=True)
    )

    op.create_index("ix_d2c_order_lines_offer_code", "d2c_order_lines", ["offer_code"])
    op.create_index("ix_d2c_order_lines_group_code", "d2c_order_lines", ["group_code"])
    op.create_index("ix_d2c_order_lines_price_code", "d2c_order_lines", ["price_code"])


def downgrade() -> None:
    op.drop_index("ix_d2c_order_lines_price_code", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_group_code", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_offer_code", table_name="d2c_order_lines")

    op.drop_column("d2c_order_lines", "source_position_id")
    op.drop_column("d2c_order_lines", "source_offer_id")
    op.drop_column("d2c_order_lines", "price_code")
    op.drop_column("d2c_order_lines", "group_name")
    op.drop_column("d2c_order_lines", "group_code")
    op.drop_column("d2c_order_lines", "offer_image_url")
    op.drop_column("d2c_order_lines", "offer_subtitle")
    op.drop_column("d2c_order_lines", "offer_type")
    op.drop_column("d2c_order_lines", "offer_title")
    op.drop_column("d2c_order_lines", "offer_code")
