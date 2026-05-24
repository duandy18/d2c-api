"""retire legacy storefront catalog owner tables.

Revision ID: 0019_retire_cat
Revises: 0018_snap
Create Date: 2026-05-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019_retire_cat"
down_revision: str | Sequence[str] | None = "0018_snap"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("d2c_sku_prices")
    op.drop_table("d2c_product_skus")
    op.drop_table("d2c_products")
    op.drop_table("d2c_price_lists")
    op.drop_table("d2c_units")
    op.drop_table("d2c_product_categories")


def downgrade() -> None:
    op.create_table(
        "d2c_product_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
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
        sa.UniqueConstraint("code", name="uq_d2c_product_categories_code"),
    )
    op.create_index(
        "ix_d2c_product_categories_code",
        "d2c_product_categories",
        ["code"],
    )

    op.create_table(
        "d2c_units",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("unit_code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("unit_type", sa.String(length=32), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=True),
        sa.Column("precision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_base_unit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("base_unit_code", sa.String(length=32), nullable=True),
        sa.Column("conversion_factor", sa.Numeric(18, 6), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("unit_code", name="uq_d2c_units_unit_code"),
        sa.CheckConstraint("precision >= 0", name="ck_d2c_units_precision_non_negative"),
        sa.CheckConstraint(
            "conversion_factor IS NULL OR conversion_factor > 0",
            name="ck_d2c_units_conversion_factor_positive",
        ),
    )
    op.create_index("ix_d2c_units_unit_code", "d2c_units", ["unit_code"])
    op.create_index("ix_d2c_units_unit_type", "d2c_units", ["unit_type"])

    op.create_table(
        "d2c_price_lists",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("price_list_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("region_code", sa.String(length=32), nullable=False, server_default="US"),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="storefront"),
        sa.Column(
            "customer_segment",
            sa.String(length=32),
            nullable=False,
            server_default="default",
        ),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("price_list_code", name="uq_d2c_price_lists_code"),
        sa.CheckConstraint("priority >= 0", name="ck_d2c_price_lists_priority_non_negative"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from",
            name="ck_d2c_price_lists_effective_range_valid",
        ),
    )
    op.create_index("ix_d2c_price_lists_channel", "d2c_price_lists", ["channel"])
    op.create_index("ix_d2c_price_lists_currency", "d2c_price_lists", ["currency"])
    op.create_index("ix_d2c_price_lists_is_default", "d2c_price_lists", ["is_default"])

    op.create_table(
        "d2c_products",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("product_code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("subtitle", sa.String(length=240), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
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
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["d2c_product_categories.id"],
            name="fk_d2c_products_category_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("product_code", name="uq_d2c_products_product_code"),
    )
    op.create_index("ix_d2c_products_product_code", "d2c_products", ["product_code"])
    op.create_index("ix_d2c_products_category_id", "d2c_products", ["category_id"])

    op.create_table(
        "d2c_product_skus",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, default="USD"),
        sa.Column("stock_status", sa.String(length=32), nullable=False, default="in_stock"),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, default=0),
        sa.Column("sales_unit_id", sa.BigInteger(), nullable=False),
        sa.Column("package_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("package_unit_text", sa.String(length=64), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["d2c_products.id"],
            name="fk_d2c_product_skus_product_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sales_unit_id"],
            ["d2c_units.id"],
            name="fk_d2c_product_skus_sales_unit_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("sku_code", name="uq_d2c_product_skus_sku_code"),
        sa.CheckConstraint(
            "package_quantity > 0",
            name="ck_d2c_product_skus_package_quantity_positive",
        ),
    )
    op.create_index("ix_d2c_product_skus_sku_code", "d2c_product_skus", ["sku_code"])
    op.create_index("ix_d2c_product_skus_product_id", "d2c_product_skus", ["product_id"])
    op.create_index(
        "ix_d2c_product_skus_sales_unit_id",
        "d2c_product_skus",
        ["sales_unit_id"],
    )

    op.create_table(
        "d2c_sku_prices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("price_list_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_id", sa.BigInteger(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("compare_at_price_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["price_list_id"],
            ["d2c_price_lists.id"],
            name="fk_d2c_sku_prices_price_list_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["d2c_product_skus.id"],
            name="fk_d2c_sku_prices_sku_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "price_list_id",
            "sku_id",
            name="uq_d2c_sku_prices_price_list_id_sku_id",
        ),
        sa.CheckConstraint(
            "price_cents >= 0",
            name="ck_d2c_sku_prices_price_cents_non_negative",
        ),
        sa.CheckConstraint(
            "compare_at_price_cents IS NULL OR compare_at_price_cents >= price_cents",
            name="ck_d2c_sku_prices_compare_at_price_valid",
        ),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from",
            name="ck_d2c_sku_prices_effective_range_valid",
        ),
    )
    op.create_index("ix_d2c_sku_prices_is_active", "d2c_sku_prices", ["is_active"])
    op.create_index("ix_d2c_sku_prices_price_list_id", "d2c_sku_prices", ["price_list_id"])
    op.create_index("ix_d2c_sku_prices_sku_id", "d2c_sku_prices", ["sku_id"])
