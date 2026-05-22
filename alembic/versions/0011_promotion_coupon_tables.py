"""add_promotion_coupon_tables.

Revision ID: 0011_promotion_coupon_tables
Revises: 0010_catalog_units_price_tables
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_promotion_coupon_tables"
down_revision: str | Sequence[str] | None = "0010_catalog_units_price_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "d2c_promotions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("promotion_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("promotion_type", sa.String(length=32), nullable=False),
        sa.Column("discount_type", sa.String(length=32), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("min_order_amount_cents", sa.Integer(), nullable=True),
        sa.Column("max_discount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("stackable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.CheckConstraint(
            "discount_value > 0",
            name="ck_d2c_promotions_discount_value_positive",
        ),
        sa.CheckConstraint(
            "discount_type <> 'percentage' OR discount_value <= 100",
            name="ck_d2c_promotions_percentage_value_valid",
        ),
        sa.CheckConstraint(
            "min_order_amount_cents IS NULL OR min_order_amount_cents >= 0",
            name="ck_d2c_promotions_min_order_amount_non_negative",
        ),
        sa.CheckConstraint(
            "max_discount_cents IS NULL OR max_discount_cents >= 0",
            name="ck_d2c_promotions_max_discount_non_negative",
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_promotions_effective_range_valid",
        ),
        sa.CheckConstraint(
            "priority >= 0",
            name="ck_d2c_promotions_priority_non_negative",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("promotion_code", name="uq_d2c_promotions_code"),
    )
    op.create_index(
        "ix_d2c_promotions_code",
        "d2c_promotions",
        ["promotion_code"],
    )
    op.create_index(
        "ix_d2c_promotions_status",
        "d2c_promotions",
        ["status"],
    )
    op.create_index(
        "ix_d2c_promotions_type",
        "d2c_promotions",
        ["promotion_type"],
    )
    op.create_index(
        "ix_d2c_promotions_active_range",
        "d2c_promotions",
        ["is_active", "starts_at", "ends_at"],
    )

    op.create_table(
        "d2c_promotion_targets",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("promotion_id", sa.BigInteger(), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("target_code", sa.String(length=96), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "target_type = 'all_store' OR target_id IS NOT NULL OR target_code IS NOT NULL",
            name="ck_d2c_promotion_targets_target_present",
        ),
        sa.ForeignKeyConstraint(
            ["promotion_id"],
            ["d2c_promotions.id"],
            name="fk_d2c_promotion_targets_promotion_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "promotion_id",
            "target_type",
            "target_id",
            "target_code",
            name="uq_d2c_promotion_targets_scope",
        ),
    )
    op.create_index(
        "ix_d2c_promotion_targets_promotion_id",
        "d2c_promotion_targets",
        ["promotion_id"],
    )
    op.create_index(
        "ix_d2c_promotion_targets_target",
        "d2c_promotion_targets",
        ["target_type", "target_id", "target_code"],
    )

    op.create_table(
        "d2c_coupons",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("coupon_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("promotion_id", sa.BigInteger(), nullable=False),
        sa.Column("coupon_type", sa.String(length=32), nullable=False),
        sa.Column("total_limit", sa.Integer(), nullable=True),
        sa.Column("per_customer_limit", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.CheckConstraint(
            "total_limit IS NULL OR total_limit > 0",
            name="ck_d2c_coupons_total_limit_positive",
        ),
        sa.CheckConstraint(
            "per_customer_limit IS NULL OR per_customer_limit > 0",
            name="ck_d2c_coupons_per_customer_limit_positive",
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_coupons_effective_range_valid",
        ),
        sa.ForeignKeyConstraint(
            ["promotion_id"],
            ["d2c_promotions.id"],
            name="fk_d2c_coupons_promotion_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coupon_code", name="uq_d2c_coupons_code"),
    )
    op.create_index("ix_d2c_coupons_code", "d2c_coupons", ["coupon_code"])
    op.create_index("ix_d2c_coupons_status", "d2c_coupons", ["status"])
    op.create_index(
        "ix_d2c_coupons_promotion_id",
        "d2c_coupons",
        ["promotion_id"],
    )

    op.create_table(
        "d2c_customer_coupons",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("customer_coupon_code", sa.String(length=96), nullable=False),
        sa.Column("coupon_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="claimed"),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "used_at IS NULL OR claimed_at IS NULL OR used_at >= claimed_at",
            name="ck_d2c_customer_coupons_used_after_claimed",
        ),
        sa.ForeignKeyConstraint(
            ["coupon_id"],
            ["d2c_coupons.id"],
            name="fk_d2c_customer_coupons_coupon_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_customer_coupons_customer_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["d2c_orders.id"],
            name="fk_d2c_customer_coupons_order_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_coupon_code",
            name="uq_d2c_customer_coupons_code",
        ),
    )
    op.create_index(
        "ix_d2c_customer_coupons_coupon_id",
        "d2c_customer_coupons",
        ["coupon_id"],
    )
    op.create_index(
        "ix_d2c_customer_coupons_customer_id",
        "d2c_customer_coupons",
        ["customer_id"],
    )
    op.create_index(
        "ix_d2c_customer_coupons_status",
        "d2c_customer_coupons",
        ["status"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_d2c_customer_coupons_status",
        table_name="d2c_customer_coupons",
    )
    op.drop_index(
        "ix_d2c_customer_coupons_customer_id",
        table_name="d2c_customer_coupons",
    )
    op.drop_index(
        "ix_d2c_customer_coupons_coupon_id",
        table_name="d2c_customer_coupons",
    )
    op.drop_table("d2c_customer_coupons")

    op.drop_index("ix_d2c_coupons_promotion_id", table_name="d2c_coupons")
    op.drop_index("ix_d2c_coupons_status", table_name="d2c_coupons")
    op.drop_index("ix_d2c_coupons_code", table_name="d2c_coupons")
    op.drop_table("d2c_coupons")

    op.drop_index(
        "ix_d2c_promotion_targets_target",
        table_name="d2c_promotion_targets",
    )
    op.drop_index(
        "ix_d2c_promotion_targets_promotion_id",
        table_name="d2c_promotion_targets",
    )
    op.drop_table("d2c_promotion_targets")

    op.drop_index("ix_d2c_promotions_active_range", table_name="d2c_promotions")
    op.drop_index("ix_d2c_promotions_type", table_name="d2c_promotions")
    op.drop_index("ix_d2c_promotions_status", table_name="d2c_promotions")
    op.drop_index("ix_d2c_promotions_code", table_name="d2c_promotions")
    op.drop_table("d2c_promotions")
