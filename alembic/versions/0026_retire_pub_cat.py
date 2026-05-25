"""retire_legacy_published_catalog.

Revision ID: 0026_retire_pub_cat
Revises: 0025_retire_pub_promo
Create Date: 2026-05-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026_retire_pub_cat"
down_revision: str | Sequence[str] | None = "0025_retire_pub_promo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("d2c_published_prices")
    op.drop_table("d2c_published_skus")
    op.drop_table("d2c_published_products")


def downgrade() -> None:
    op.create_table(
        "d2c_published_products",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
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
        sa.Column("display_status", sa.String(length=32), server_default="hidden", nullable=False),
        sa.Column(
            "sell_status", sa.String(length=32), server_default="not_sellable", nullable=False
        ),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_product_id", sa.BigInteger(), nullable=True),
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
            "sort_order >= 0", name="ck_d2c_published_products_sort_order_non_negative"
        ),
        sa.CheckConstraint(
            "visible_until IS NULL OR visible_from IS NULL OR visible_until > visible_from",
            name="ck_d2c_published_products_visible_range_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publish_version", "product_code", name="uq_d2c_published_products_version_product"
        ),
    )
    op.create_index(
        "ix_d2c_published_products_product_code", "d2c_published_products", ["product_code"]
    )
    op.create_index(
        "ix_d2c_published_products_version_visibility",
        "d2c_published_products",
        ["publish_version", "display_status", "sell_status"],
    )
    op.create_index(
        "ix_d2c_published_products_category", "d2c_published_products", ["category_code"]
    )

    op.create_table(
        "d2c_published_skus",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("product_code", sa.String(length=96), nullable=False),
        sa.Column("sku_code", sa.String(length=128), nullable=False),
        sa.Column("sku_name", sa.String(length=200), nullable=False),
        sa.Column("display_sku_name", sa.String(length=200), nullable=False),
        sa.Column("sales_unit_code", sa.String(length=64), nullable=True),
        sa.Column("sales_unit_name", sa.String(length=120), nullable=True),
        sa.Column("barcode", sa.String(length=128), nullable=True),
        sa.Column("spec_text", sa.String(length=240), nullable=True),
        sa.Column("is_sellable", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_sku_id", sa.BigInteger(), nullable=True),
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
        sa.CheckConstraint("sort_order >= 0", name="ck_d2c_published_skus_sort_order_non_negative"),
        sa.ForeignKeyConstraint(
            ["publish_version", "product_code"],
            ["d2c_published_products.publish_version", "d2c_published_products.product_code"],
            name="fk_d2c_published_skus_product_version",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publish_version", "sku_code", name="uq_d2c_published_skus_version_sku"
        ),
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
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("price_list_code", sa.String(length=96), nullable=False),
        sa.Column("channel", sa.String(length=32), server_default="storefront", nullable=False),
        sa.Column("sku_code", sa.String(length=128), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("compare_at_price_cents", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_price_id", sa.BigInteger(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
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
