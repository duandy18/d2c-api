"""add offer display metrics

Revision ID: 0032_disp_metrics
Revises: 0031_pub_src
Create Date: 2026-05-29 10:20:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0032_disp_metrics"
down_revision: str | Sequence[str] | None = "0031_pub_src"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "d2c_offer_display_metrics",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column(
            "display_sold_quantity",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "display_paid_customer_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "display_stock_quantity",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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
        sa.UniqueConstraint("offer_code", name="uq_d2c_offer_disp_metrics_offer"),
        sa.CheckConstraint(
            "display_sold_quantity >= 0",
            name="ck_d2c_offer_disp_sold_non_negative",
        ),
        sa.CheckConstraint(
            "display_paid_customer_count >= 0",
            name="ck_d2c_offer_disp_paid_non_negative",
        ),
        sa.CheckConstraint(
            "display_stock_quantity >= 0",
            name="ck_d2c_offer_disp_stock_non_negative",
        ),
    )
    op.create_index(
        "ix_d2c_offer_disp_metrics_offer",
        "d2c_offer_display_metrics",
        ["offer_code"],
    )
    op.create_index(
        "ix_d2c_offer_disp_metrics_active",
        "d2c_offer_display_metrics",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_d2c_offer_disp_metrics_active",
        table_name="d2c_offer_display_metrics",
    )
    op.drop_index(
        "ix_d2c_offer_disp_metrics_offer",
        table_name="d2c_offer_display_metrics",
    )
    op.drop_table("d2c_offer_display_metrics")
