"""add_catalog_units_price_tables.

Revision ID: 0010_catalog_units_price_tables
Revises: 0009_checkout_payment_model
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_catalog_units_price_tables"
down_revision: str | Sequence[str] | None = "0009_checkout_payment_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "d2c_units",
        sa.Column("id", sa.BigInteger(), nullable=False),
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
        sa.CheckConstraint("precision >= 0", name="ck_d2c_units_precision_non_negative"),
        sa.CheckConstraint(
            "conversion_factor IS NULL OR conversion_factor > 0",
            name="ck_d2c_units_conversion_factor_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("unit_code", name="uq_d2c_units_unit_code"),
    )
    op.create_index("ix_d2c_units_unit_code", "d2c_units", ["unit_code"])
    op.create_index("ix_d2c_units_unit_type", "d2c_units", ["unit_type"])

    op.execute(
        """
        INSERT INTO d2c_units (
          unit_code,
          name,
          unit_type,
          symbol,
          precision,
          is_base_unit,
          base_unit_code,
          conversion_factor,
          is_active,
          sort_order
        )
        VALUES
          ('piece', '件', 'count', '件', 0, TRUE, NULL, NULL, TRUE, 10),
          ('sheet', '片', 'count', '片', 0, FALSE, 'piece', 1, TRUE, 20),
          ('pack', '包', 'package', '包', 0, TRUE, NULL, NULL, TRUE, 30),
          ('bag', '袋', 'package', '袋', 0, TRUE, NULL, NULL, TRUE, 40),
          ('g', '克', 'weight', 'g', 0, TRUE, NULL, NULL, TRUE, 50),
          ('kg', '千克', 'weight', 'kg', 3, FALSE, 'g', 1000, TRUE, 60),
          ('ml', '毫升', 'volume', 'ml', 0, TRUE, NULL, NULL, TRUE, 70),
          ('l', '升', 'volume', 'L', 3, FALSE, 'ml', 1000, TRUE, 80)
        """
    )

    op.add_column(
        "d2c_product_skus",
        sa.Column("sales_unit_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "d2c_product_skus",
        sa.Column("package_quantity", sa.Numeric(18, 6), nullable=True),
    )
    op.add_column(
        "d2c_product_skus",
        sa.Column("package_unit_text", sa.String(length=64), nullable=True),
    )

    op.execute(
        """
        UPDATE d2c_product_skus s
        SET
          sales_unit_id = u.id,
          package_quantity = v.package_quantity,
          package_unit_text = v.package_unit_text
        FROM (
          VALUES
            ('CAT-FOOD-SALMON-1KG', 'bag', 1::numeric, '1kg'),
            ('CAT-LITTER-TOFU-6L', 'bag', 6::numeric, '6L'),
            ('CAT-TREAT-CHICKEN-80G', 'pack', 80::numeric, '80g'),
            ('CAT-TOY-FEATHER', 'piece', 1::numeric, '1件'),
            ('PET-CARE-WIPES-80', 'pack', 80::numeric, '80片'),
            ('PET-TRAVEL-BOWL', 'piece', 1::numeric, '1件')
        ) AS v(sku_code, unit_code, package_quantity, package_unit_text)
        JOIN d2c_units u
          ON u.unit_code = v.unit_code
        WHERE s.sku_code = v.sku_code
        """
    )

    op.alter_column(
        "d2c_product_skus",
        "sales_unit_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "d2c_product_skus",
        "package_quantity",
        existing_type=sa.Numeric(18, 6),
        nullable=False,
    )
    op.alter_column(
        "d2c_product_skus",
        "package_unit_text",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_d2c_product_skus_sales_unit_id",
        "d2c_product_skus",
        "d2c_units",
        ["sales_unit_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_d2c_product_skus_sales_unit_id",
        "d2c_product_skus",
        ["sales_unit_id"],
    )
    op.create_check_constraint(
        "ck_d2c_product_skus_package_quantity_positive",
        "d2c_product_skus",
        "package_quantity > 0",
    )

    op.create_table(
        "d2c_price_lists",
        sa.Column("id", sa.BigInteger(), nullable=False),
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
        sa.CheckConstraint("priority >= 0", name="ck_d2c_price_lists_priority_non_negative"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from",
            name="ck_d2c_price_lists_effective_range_valid",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("price_list_code", name="uq_d2c_price_lists_code"),
    )
    op.create_index("ix_d2c_price_lists_channel", "d2c_price_lists", ["channel"])
    op.create_index("ix_d2c_price_lists_currency", "d2c_price_lists", ["currency"])
    op.create_index("ix_d2c_price_lists_is_default", "d2c_price_lists", ["is_default"])

    op.execute(
        """
        INSERT INTO d2c_price_lists (
          price_list_code,
          name,
          currency,
          region_code,
          channel,
          customer_segment,
          priority,
          is_default,
          is_active
        )
        VALUES (
          'default_usd_storefront',
          '默认美元前台价',
          'USD',
          'US',
          'storefront',
          'default',
          100,
          TRUE,
          TRUE
        )
        """
    )

    op.create_table(
        "d2c_sku_prices",
        sa.Column("id", sa.BigInteger(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "price_list_id",
            "sku_id",
            name="uq_d2c_sku_prices_price_list_id_sku_id",
        ),
    )
    op.create_index("ix_d2c_sku_prices_is_active", "d2c_sku_prices", ["is_active"])
    op.create_index("ix_d2c_sku_prices_price_list_id", "d2c_sku_prices", ["price_list_id"])
    op.create_index("ix_d2c_sku_prices_sku_id", "d2c_sku_prices", ["sku_id"])

    op.execute(
        """
        INSERT INTO d2c_sku_prices (
          price_list_id,
          sku_id,
          price_cents,
          compare_at_price_cents,
          currency,
          is_active
        )
        SELECT
          pl.id,
          s.id,
          s.price_cents,
          NULL,
          s.currency,
          TRUE
        FROM d2c_product_skus s
        CROSS JOIN d2c_price_lists pl
        WHERE pl.price_list_code = 'default_usd_storefront'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_d2c_sku_prices_sku_id", table_name="d2c_sku_prices")
    op.drop_index("ix_d2c_sku_prices_price_list_id", table_name="d2c_sku_prices")
    op.drop_index("ix_d2c_sku_prices_is_active", table_name="d2c_sku_prices")
    op.drop_table("d2c_sku_prices")

    op.drop_index("ix_d2c_price_lists_is_default", table_name="d2c_price_lists")
    op.drop_index("ix_d2c_price_lists_currency", table_name="d2c_price_lists")
    op.drop_index("ix_d2c_price_lists_channel", table_name="d2c_price_lists")
    op.drop_table("d2c_price_lists")

    op.drop_constraint(
        "ck_d2c_product_skus_package_quantity_positive",
        "d2c_product_skus",
        type_="check",
    )
    op.drop_index("ix_d2c_product_skus_sales_unit_id", table_name="d2c_product_skus")
    op.drop_constraint(
        "fk_d2c_product_skus_sales_unit_id",
        "d2c_product_skus",
        type_="foreignkey",
    )
    op.drop_column("d2c_product_skus", "package_unit_text")
    op.drop_column("d2c_product_skus", "package_quantity")
    op.drop_column("d2c_product_skus", "sales_unit_id")

    op.drop_index("ix_d2c_units_unit_type", table_name="d2c_units")
    op.drop_index("ix_d2c_units_unit_code", table_name="d2c_units")
    op.drop_table("d2c_units")
