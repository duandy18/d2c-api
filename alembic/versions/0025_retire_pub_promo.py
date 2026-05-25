"""retire_legacy_published_promotions.

Revision ID: 0025_retire_pub_promo
Revises: 0024_order_offer_rt
Create Date: 2026-05-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0025_retire_pub_promo"
down_revision: str | Sequence[str] | None = "0024_order_offer_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("d2c_published_promotions")


def downgrade() -> None:
    op.create_table(
        "d2c_published_promotions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("promotion_code", sa.String(length=64), nullable=False),
        sa.Column("promotion_name", sa.String(length=160), nullable=False),
        sa.Column("promotion_type", sa.String(length=32), nullable=False),
        sa.Column("discount_type", sa.String(length=32), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("min_order_amount_cents", sa.Integer(), nullable=True),
        sa.Column("max_discount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("stackable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_promotion_id", sa.BigInteger(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
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
            "discount_value > 0", name="ck_d2c_published_promotions_discount_positive"
        ),
        sa.CheckConstraint(
            "discount_type <> 'percentage' OR discount_value <= 100",
            name="ck_d2c_published_promotions_percentage_valid",
        ),
        sa.CheckConstraint(
            "min_order_amount_cents IS NULL OR min_order_amount_cents >= 0",
            name="ck_d2c_published_promotions_min_order_non_negative",
        ),
        sa.CheckConstraint(
            "max_discount_cents IS NULL OR max_discount_cents >= 0",
            name="ck_d2c_published_promotions_max_discount_non_negative",
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_published_promotions_effective_range_valid",
        ),
        sa.CheckConstraint(
            "priority >= 0", name="ck_d2c_published_promotions_priority_non_negative"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publish_version", "promotion_code", name="uq_d2c_published_promotions_version_code"
        ),
    )
    op.create_index(
        "ix_d2c_published_promotions_code", "d2c_published_promotions", ["promotion_code"]
    )
    op.create_index(
        "ix_d2c_published_promotions_runtime",
        "d2c_published_promotions",
        ["publish_version", "is_active", "starts_at", "ends_at"],
    )
