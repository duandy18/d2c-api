"""add_terminal_published_snapshot_runtime_tables.

Revision ID: 0021_pub_snapshot_rt
Revises: 0020_promo_exec
Create Date: 2026-05-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021_pub_snapshot_rt"
down_revision: str | Sequence[str] | None = "0020_promo_exec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "d2c_published_groups",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("group_code", sa.String(length=96), nullable=False),
        sa.Column("group_name", sa.String(length=160), nullable=False),
        sa.Column("group_kind", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("display_status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("source_group_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("publish_version", "group_code", name="uq_d2c_pub_groups_code"),
    )
    op.create_index(
        "ix_d2c_pub_groups_version_sort", "d2c_published_groups", ["publish_version", "sort_order"]
    )

    op.create_table(
        "d2c_published_offers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column("offer_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("subtitle", sa.String(length=240), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("display_status", sa.String(length=32), nullable=False),
        sa.Column("sell_status", sa.String(length=32), nullable=False),
        sa.Column("source_offer_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("publish_version", "offer_code", name="uq_d2c_pub_offers_code"),
    )
    op.create_index(
        "ix_d2c_pub_offers_version_type", "d2c_published_offers", ["publish_version", "offer_type"]
    )
    op.create_index(
        "ix_d2c_pub_offers_sellable",
        "d2c_published_offers",
        ["publish_version", "display_status", "sell_status"],
    )

    op.create_table(
        "d2c_published_offer_components",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column("component_no", sa.Integer(), nullable=False),
        sa.Column("pms_item_id", sa.BigInteger(), nullable=False),
        sa.Column("pms_sku", sa.String(length=128), nullable=False),
        sa.Column("pms_sku_code_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_code", sa.String(length=128), nullable=False),
        sa.Column("pms_item_uom_id", sa.BigInteger(), nullable=False),
        sa.Column("uom_code", sa.String(length=32), nullable=False),
        sa.Column("uom_name", sa.String(length=80), nullable=False),
        sa.Column("pms_barcode_id", sa.BigInteger(), nullable=True),
        sa.Column("barcode", sa.String(length=128), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("component_role", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("source_component_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publish_version", "offer_code", "component_no", name="uq_d2c_pub_components_no"
        ),
    )
    op.create_index(
        "ix_d2c_pub_components_offer",
        "d2c_published_offer_components",
        ["publish_version", "offer_code"],
    )
    op.create_index(
        "ix_d2c_pub_components_pms_item", "d2c_published_offer_components", ["pms_item_id"]
    )

    op.create_table(
        "d2c_published_offer_prices",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column("price_code", sa.String(length=96), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("compare_at_price_cents", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("source_price_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("publish_version", "price_code", name="uq_d2c_pub_prices_code"),
    )
    op.create_index(
        "ix_d2c_pub_prices_offer",
        "d2c_published_offer_prices",
        ["publish_version", "offer_code", "is_active"],
    )

    op.create_table(
        "d2c_published_offer_positions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("position_code", sa.String(length=120), nullable=False),
        sa.Column("group_code", sa.String(length=96), nullable=False),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("position_source", sa.String(length=32), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("source_position_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("publish_version", "position_code", name="uq_d2c_pub_positions_code"),
    )
    op.create_index(
        "ix_d2c_pub_positions_group",
        "d2c_published_offer_positions",
        ["publish_version", "group_code", "sort_order"],
    )
    op.create_index(
        "ix_d2c_pub_positions_offer",
        "d2c_published_offer_positions",
        ["publish_version", "offer_code"],
    )

    op.create_table(
        "d2c_published_promotion_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("promotion_code", sa.String(length=64), nullable=False),
        sa.Column("promotion_name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("promotion_type", sa.String(length=32), nullable=False),
        sa.Column("discount_type", sa.String(length=32), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("threshold_amount_cents", sa.Integer(), nullable=True),
        sa.Column("max_discount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("stackable", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("display_badge", sa.String(length=64), nullable=True),
        sa.Column("source_promotion_rule_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("publish_version", "promotion_code", name="uq_d2c_pub_rules_code"),
    )
    op.create_index(
        "ix_d2c_pub_rules_active", "d2c_published_promotion_rules", ["publish_version", "is_active"]
    )

    op.create_table(
        "d2c_published_promotion_targets",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("promotion_code", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("target_code", sa.String(length=96), nullable=True),
        sa.Column("source_target_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publish_version",
            "promotion_code",
            "target_type",
            "target_code",
            "target_id",
            name="uq_d2c_pub_targets_scope",
        ),
    )
    op.create_index(
        "ix_d2c_pub_targets_rule",
        "d2c_published_promotion_targets",
        ["publish_version", "promotion_code"],
    )
    op.create_index(
        "ix_d2c_pub_targets_target",
        "d2c_published_promotion_targets",
        ["publish_version", "target_type", "target_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_pub_targets_target", table_name="d2c_published_promotion_targets")
    op.drop_index("ix_d2c_pub_targets_rule", table_name="d2c_published_promotion_targets")
    op.drop_table("d2c_published_promotion_targets")

    op.drop_index("ix_d2c_pub_rules_active", table_name="d2c_published_promotion_rules")
    op.drop_table("d2c_published_promotion_rules")

    op.drop_index("ix_d2c_pub_positions_offer", table_name="d2c_published_offer_positions")
    op.drop_index("ix_d2c_pub_positions_group", table_name="d2c_published_offer_positions")
    op.drop_table("d2c_published_offer_positions")

    op.drop_index("ix_d2c_pub_prices_offer", table_name="d2c_published_offer_prices")
    op.drop_table("d2c_published_offer_prices")

    op.drop_index("ix_d2c_pub_components_pms_item", table_name="d2c_published_offer_components")
    op.drop_index("ix_d2c_pub_components_offer", table_name="d2c_published_offer_components")
    op.drop_table("d2c_published_offer_components")

    op.drop_index("ix_d2c_pub_offers_sellable", table_name="d2c_published_offers")
    op.drop_index("ix_d2c_pub_offers_version_type", table_name="d2c_published_offers")
    op.drop_table("d2c_published_offers")

    op.drop_index("ix_d2c_pub_groups_version_sort", table_name="d2c_published_groups")
    op.drop_table("d2c_published_groups")
