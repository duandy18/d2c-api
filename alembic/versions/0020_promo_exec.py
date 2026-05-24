"""switch checkout promotion coupon execution to published model.

Revision ID: 0020_promo_exec
Revises: 0019_retire_cat
Create Date: 2026-05-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_promo_exec"
down_revision: str | Sequence[str] | None = "0019_retire_cat"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CUSTOMER_COUPON_SNAPSHOT_COLUMNS = [
    sa.Column("publish_version", sa.String(length=64), nullable=True),
    sa.Column("coupon_code", sa.String(length=64), nullable=True),
    sa.Column("coupon_name", sa.String(length=160), nullable=True),
    sa.Column("coupon_type", sa.String(length=32), nullable=True),
    sa.Column("promotion_code", sa.String(length=64), nullable=True),
    sa.Column("promotion_name", sa.String(length=160), nullable=True),
    sa.Column("promotion_type", sa.String(length=32), nullable=True),
    sa.Column("promotion_discount_type", sa.String(length=32), nullable=True),
    sa.Column("promotion_discount_value", sa.Integer(), nullable=True),
    sa.Column("order_no", sa.String(length=32), nullable=True),
]


def _timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    for column in CUSTOMER_COUPON_SNAPSHOT_COLUMNS:
        op.add_column("d2c_customer_coupons", column.copy())

    op.execute(
        """
        UPDATE d2c_customer_coupons cc
        SET
          coupon_code = c.coupon_code,
          coupon_name = c.name,
          coupon_type = c.coupon_type,
          promotion_code = p.promotion_code,
          promotion_name = p.name,
          promotion_type = p.promotion_type,
          promotion_discount_type = p.discount_type,
          promotion_discount_value = p.discount_value,
          order_no = (
            SELECT o.order_no
            FROM d2c_orders o
            WHERE o.id = cc.order_id
          )
        FROM d2c_coupons c
        JOIN d2c_promotions p
          ON p.id = c.promotion_id
        WHERE cc.coupon_id = c.id
        """
    )

    op.drop_constraint(
        "fk_d2c_customer_coupons_coupon_id",
        "d2c_customer_coupons",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_d2c_orders_coupon_id",
        "d2c_orders",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_d2c_orders_promotion_id",
        "d2c_orders",
        type_="foreignkey",
    )

    op.drop_index("ix_d2c_customer_coupons_coupon_id", table_name="d2c_customer_coupons")
    op.drop_index("ix_d2c_orders_coupon_id", table_name="d2c_orders")
    op.drop_index("ix_d2c_orders_promotion_id", table_name="d2c_orders")

    op.drop_column("d2c_customer_coupons", "coupon_id")
    op.drop_column("d2c_orders", "coupon_id")
    op.drop_column("d2c_orders", "promotion_id")

    op.drop_index("ix_d2c_coupons_promotion_id", table_name="d2c_coupons")
    op.drop_index("ix_d2c_coupons_status", table_name="d2c_coupons")
    op.drop_index("ix_d2c_coupons_code", table_name="d2c_coupons")
    op.drop_table("d2c_coupons")

    op.drop_index("ix_d2c_promotion_targets_target", table_name="d2c_promotion_targets")
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

    op.create_index(
        "ix_d2c_customer_coupons_publish_version",
        "d2c_customer_coupons",
        ["publish_version"],
    )
    op.create_index(
        "ix_d2c_customer_coupons_coupon_code",
        "d2c_customer_coupons",
        ["coupon_code"],
    )
    op.create_index(
        "ix_d2c_customer_coupons_promotion_code",
        "d2c_customer_coupons",
        ["promotion_code"],
    )
    op.create_index(
        "ix_d2c_customer_coupons_order_no",
        "d2c_customer_coupons",
        ["order_no"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_customer_coupons_order_no", table_name="d2c_customer_coupons")
    op.drop_index(
        "ix_d2c_customer_coupons_promotion_code",
        table_name="d2c_customer_coupons",
    )
    op.drop_index(
        "ix_d2c_customer_coupons_coupon_code",
        table_name="d2c_customer_coupons",
    )
    op.drop_index(
        "ix_d2c_customer_coupons_publish_version",
        table_name="d2c_customer_coupons",
    )

    op.create_table(
        "d2c_promotions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
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
        _timestamp_column("created_at"),
        _timestamp_column("updated_at"),
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
        sa.UniqueConstraint("promotion_code", name="uq_d2c_promotions_code"),
    )
    op.create_index("ix_d2c_promotions_code", "d2c_promotions", ["promotion_code"])
    op.create_index("ix_d2c_promotions_status", "d2c_promotions", ["status"])
    op.create_index("ix_d2c_promotions_type", "d2c_promotions", ["promotion_type"])
    op.create_index(
        "ix_d2c_promotions_active_range",
        "d2c_promotions",
        ["is_active", "starts_at", "ends_at"],
    )

    op.create_table(
        "d2c_promotion_targets",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("promotion_id", sa.BigInteger(), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("target_code", sa.String(length=96), nullable=True),
        _timestamp_column("created_at"),
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
        sa.Column("id", sa.BigInteger(), primary_key=True),
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
        _timestamp_column("created_at"),
        _timestamp_column("updated_at"),
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
        sa.UniqueConstraint("coupon_code", name="uq_d2c_coupons_code"),
    )
    op.create_index("ix_d2c_coupons_code", "d2c_coupons", ["coupon_code"])
    op.create_index("ix_d2c_coupons_status", "d2c_coupons", ["status"])
    op.create_index("ix_d2c_coupons_promotion_id", "d2c_coupons", ["promotion_id"])

    op.add_column(
        "d2c_orders",
        sa.Column("promotion_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_orders",
        sa.Column("coupon_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_customer_coupons",
        sa.Column("coupon_id", sa.BigInteger(), nullable=True),
    )

    op.create_index("ix_d2c_orders_promotion_id", "d2c_orders", ["promotion_id"])
    op.create_index("ix_d2c_orders_coupon_id", "d2c_orders", ["coupon_id"])
    op.create_index(
        "ix_d2c_customer_coupons_coupon_id",
        "d2c_customer_coupons",
        ["coupon_id"],
    )

    for column in reversed(CUSTOMER_COUPON_SNAPSHOT_COLUMNS):
        op.drop_column("d2c_customer_coupons", column.name)
