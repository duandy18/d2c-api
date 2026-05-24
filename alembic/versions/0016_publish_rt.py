# ruff: noqa: E501
"""add runtime published model tables.

Revision ID: 0016_publish_rt
Revises: 0015_retire_bo_pages
Create Date: 2026-05-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_publish_rt"
down_revision: str | Sequence[str] | None = "0015_retire_bo_pages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


def upgrade() -> None:
    op.create_table(
        "d2c_published_products",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("pms_item_id", sa.BigInteger(), nullable=True),
        sa.Column("pms_sku", sa.String(length=128), nullable=True),
        sa.Column("product_code", sa.String(length=96), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("category_code", sa.String(length=96), nullable=True),
        sa.Column("category_name", sa.String(length=160), nullable=True),
        sa.Column("brand_code", sa.String(length=96), nullable=True),
        sa.Column("brand_name", sa.String(length=160), nullable=True),
        sa.Column("display_status", sa.String(length=32), nullable=False, server_default="hidden"),
        sa.Column("sell_status", sa.String(length=32), nullable=False, server_default="not_sellable"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_product_id", sa.BigInteger(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.CheckConstraint("sort_order >= 0", name="ck_d2c_published_products_sort_order_non_negative"),
        sa.CheckConstraint(
            "visible_until IS NULL OR visible_from IS NULL OR visible_until > visible_from",
            name="ck_d2c_published_products_visible_range_valid",
        ),
        sa.UniqueConstraint(
            "publish_version",
            "product_code",
            name="uq_d2c_published_products_version_product",
        ),
    )
    op.create_index("ix_d2c_published_products_product_code", "d2c_published_products", ["product_code"])
    op.create_index(
        "ix_d2c_published_products_version_visibility",
        "d2c_published_products",
        ["publish_version", "display_status", "sell_status"],
    )
    op.create_index("ix_d2c_published_products_category", "d2c_published_products", ["category_code"])

    op.create_table(
        "d2c_published_skus",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("product_code", sa.String(length=96), nullable=False),
        sa.Column("sku_code", sa.String(length=128), nullable=False),
        sa.Column("sku_name", sa.String(length=200), nullable=False),
        sa.Column("display_sku_name", sa.String(length=200), nullable=False),
        sa.Column("sales_unit_code", sa.String(length=64), nullable=True),
        sa.Column("sales_unit_name", sa.String(length=120), nullable=True),
        sa.Column("barcode", sa.String(length=128), nullable=True),
        sa.Column("spec_text", sa.String(length=240), nullable=True),
        sa.Column("is_sellable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_sku_id", sa.BigInteger(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.CheckConstraint("sort_order >= 0", name="ck_d2c_published_skus_sort_order_non_negative"),
        sa.ForeignKeyConstraint(
            ["publish_version", "product_code"],
            ["d2c_published_products.publish_version", "d2c_published_products.product_code"],
            name="fk_d2c_published_skus_product_version",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("publish_version", "sku_code", name="uq_d2c_published_skus_version_sku"),
    )
    op.create_index("ix_d2c_published_skus_product_code", "d2c_published_skus", ["product_code"])
    op.create_index("ix_d2c_published_skus_sku_code", "d2c_published_skus", ["sku_code"])
    op.create_index(
        "ix_d2c_published_skus_version_sellable",
        "d2c_published_skus",
        ["publish_version", "is_sellable"],
    )

    op.create_table(
        "d2c_published_prices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("price_list_code", sa.String(length=96), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="storefront"),
        sa.Column("sku_code", sa.String(length=128), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("compare_at_price_cents", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_price_id", sa.BigInteger(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.CheckConstraint("price_cents >= 0", name="ck_d2c_published_prices_price_non_negative"),
        sa.CheckConstraint("priority >= 0", name="ck_d2c_published_prices_priority_non_negative"),
        sa.CheckConstraint(
            "compare_at_price_cents IS NULL OR compare_at_price_cents >= price_cents",
            name="ck_d2c_published_prices_compare_at_valid",
        ),
        sa.CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL OR effective_until > effective_from",
            name="ck_d2c_published_prices_effective_range_valid",
        ),
        sa.ForeignKeyConstraint(
            ["publish_version", "sku_code"],
            ["d2c_published_skus.publish_version", "d2c_published_skus.sku_code"],
            name="fk_d2c_published_prices_sku_version",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "publish_version",
            "price_list_code",
            "channel",
            "sku_code",
            name="uq_d2c_published_prices_version_list_channel_sku",
        ),
    )
    op.create_index(
        "ix_d2c_published_prices_sku_channel_active",
        "d2c_published_prices",
        ["sku_code", "channel", "is_active"],
    )
    op.create_index(
        "ix_d2c_published_prices_version_priority",
        "d2c_published_prices",
        ["publish_version", "priority"],
    )

    op.create_table(
        "d2c_published_promotions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("promotion_code", sa.String(length=64), nullable=False),
        sa.Column("promotion_name", sa.String(length=160), nullable=False),
        sa.Column("promotion_type", sa.String(length=32), nullable=False),
        sa.Column("discount_type", sa.String(length=32), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("scope_type", sa.String(length=32), nullable=False),
        sa.Column("min_order_amount_cents", sa.Integer(), nullable=True),
        sa.Column("max_discount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("stackable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_promotion_id", sa.BigInteger(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.CheckConstraint("discount_value > 0", name="ck_d2c_published_promotions_discount_positive"),
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
        sa.CheckConstraint("priority >= 0", name="ck_d2c_published_promotions_priority_non_negative"),
        sa.UniqueConstraint(
            "publish_version",
            "promotion_code",
            name="uq_d2c_published_promotions_version_code",
        ),
    )
    op.create_index("ix_d2c_published_promotions_code", "d2c_published_promotions", ["promotion_code"])
    op.create_index(
        "ix_d2c_published_promotions_runtime",
        "d2c_published_promotions",
        ["publish_version", "is_active", "starts_at", "ends_at"],
    )

    op.create_table(
        "d2c_published_coupons",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("coupon_code", sa.String(length=64), nullable=False),
        sa.Column("coupon_name", sa.String(length=160), nullable=False),
        sa.Column("promotion_code", sa.String(length=64), nullable=False),
        sa.Column("coupon_type", sa.String(length=32), nullable=False),
        sa.Column("total_limit", sa.Integer(), nullable=True),
        sa.Column("per_customer_limit", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_coupon_id", sa.BigInteger(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.CheckConstraint("total_limit IS NULL OR total_limit > 0", name="ck_d2c_published_coupons_total_limit_positive"),
        sa.CheckConstraint(
            "per_customer_limit IS NULL OR per_customer_limit > 0",
            name="ck_d2c_published_coupons_per_customer_limit_positive",
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_published_coupons_effective_range_valid",
        ),
        sa.ForeignKeyConstraint(
            ["publish_version", "promotion_code"],
            ["d2c_published_promotions.publish_version", "d2c_published_promotions.promotion_code"],
            name="fk_d2c_published_coupons_promotion_version",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("publish_version", "coupon_code", name="uq_d2c_published_coupons_version_code"),
    )
    op.create_index("ix_d2c_published_coupons_code", "d2c_published_coupons", ["coupon_code"])
    op.create_index(
        "ix_d2c_published_coupons_runtime",
        "d2c_published_coupons",
        ["publish_version", "is_active", "starts_at", "ends_at"],
    )

    op.create_table(
        "d2c_publish_sync_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("sync_scope", sa.String(length=32), nullable=False),
        sa.Column("source_service", sa.String(length=64), nullable=False, server_default="d2c-backoffice-api"),
        sa.Column("source_base_url", sa.String(length=240), nullable=True),
        sa.Column("source_endpoint", sa.String(length=240), nullable=True),
        sa.Column("publish_version", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_by", sa.String(length=120), nullable=True),
        sa.Column("rows_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_upserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_summary", sa.JSON(), nullable=True),
        sa.CheckConstraint("rows_fetched >= 0", name="ck_d2c_publish_sync_runs_rows_fetched_non_negative"),
        sa.CheckConstraint("rows_upserted >= 0", name="ck_d2c_publish_sync_runs_rows_upserted_non_negative"),
        sa.CheckConstraint("rows_deleted >= 0", name="ck_d2c_publish_sync_runs_rows_deleted_non_negative"),
    )
    op.create_index(
        "ix_d2c_publish_sync_runs_scope_status",
        "d2c_publish_sync_runs",
        ["sync_scope", "status"],
    )
    op.create_index(
        "ix_d2c_publish_sync_runs_publish_version",
        "d2c_publish_sync_runs",
        ["publish_version"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_publish_sync_runs_publish_version", table_name="d2c_publish_sync_runs")
    op.drop_index("ix_d2c_publish_sync_runs_scope_status", table_name="d2c_publish_sync_runs")
    op.drop_table("d2c_publish_sync_runs")

    op.drop_index("ix_d2c_published_coupons_runtime", table_name="d2c_published_coupons")
    op.drop_index("ix_d2c_published_coupons_code", table_name="d2c_published_coupons")
    op.drop_table("d2c_published_coupons")

    op.drop_index("ix_d2c_published_promotions_runtime", table_name="d2c_published_promotions")
    op.drop_index("ix_d2c_published_promotions_code", table_name="d2c_published_promotions")
    op.drop_table("d2c_published_promotions")

    op.drop_index("ix_d2c_published_prices_version_priority", table_name="d2c_published_prices")
    op.drop_index("ix_d2c_published_prices_sku_channel_active", table_name="d2c_published_prices")
    op.drop_table("d2c_published_prices")

    op.drop_index("ix_d2c_published_skus_version_sellable", table_name="d2c_published_skus")
    op.drop_index("ix_d2c_published_skus_sku_code", table_name="d2c_published_skus")
    op.drop_index("ix_d2c_published_skus_product_code", table_name="d2c_published_skus")
    op.drop_table("d2c_published_skus")

    op.drop_index("ix_d2c_published_products_category", table_name="d2c_published_products")
    op.drop_index("ix_d2c_published_products_version_visibility", table_name="d2c_published_products")
    op.drop_index("ix_d2c_published_products_product_code", table_name="d2c_published_products")
    op.drop_table("d2c_published_products")
