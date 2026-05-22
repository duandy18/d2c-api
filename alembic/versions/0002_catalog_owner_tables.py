"""catalog owner tables

Revision ID: 0002_catalog_owner_tables
Revises: 0001_d2c_baseline
Create Date: 2026-05-22

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_catalog_owner_tables"
down_revision: str | Sequence[str] | None = "0001_d2c_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "d2c_product_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("code", name="uq_d2c_product_categories_code"),
    )
    op.create_index(
        "ix_d2c_product_categories_code",
        "d2c_product_categories",
        ["code"],
    )

    op.create_table(
        "d2c_products",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("product_code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("subtitle", sa.String(length=240), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
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
            ["category_id"],
            ["d2c_product_categories.id"],
            name="fk_d2c_products_category_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("product_code", name="uq_d2c_products_product_code"),
    )
    op.create_index("ix_d2c_products_category_id", "d2c_products", ["category_id"])
    op.create_index("ix_d2c_products_product_code", "d2c_products", ["product_code"])

    op.create_table(
        "d2c_product_skus",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("sku_code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("stock_status", sa.String(length=32), nullable=False, server_default="in_stock"),
        sa.Column("image_url", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["d2c_products.id"],
            name="fk_d2c_product_skus_product_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("sku_code", name="uq_d2c_product_skus_sku_code"),
    )
    op.create_index("ix_d2c_product_skus_product_id", "d2c_product_skus", ["product_id"])
    op.create_index("ix_d2c_product_skus_sku_code", "d2c_product_skus", ["sku_code"])

    op.execute(
        """
        INSERT INTO d2c_product_categories (code, name, sort_order)
        VALUES
          ('cat_food', '猫粮', 10),
          ('cat_litter', '猫砂', 20),
          ('treats', '零食', 30),
          ('toys', '玩具', 40),
          ('care', '护理用品', 50),
          ('daily_travel', '出行与日用品', 60)
        """
    )

    op.execute(
        """
        INSERT INTO d2c_products (
          product_code, name, subtitle, description, category_id, status, is_active
        )
        VALUES
          (
            'pet-cat-food-salmon-001',
            '三文鱼成猫粮 1kg',
            '三文鱼风味日常主粮',
            '面向成猫的三文鱼风味日常主粮，D2C 自有商城商品。',
            (SELECT id FROM d2c_product_categories WHERE code = 'cat_food'),
            'active',
            TRUE
          ),
          (
            'pet-cat-litter-tofu-001',
            '豆腐猫砂 6L',
            '低尘豆腐猫砂',
            '低尘豆腐猫砂，适合日常猫砂盆使用。',
            (SELECT id FROM d2c_product_categories WHERE code = 'cat_litter'),
            'active',
            TRUE
          ),
          (
            'pet-cat-treat-chicken-001',
            '鸡肉冻干零食 80g',
            '高蛋白鸡肉冻干',
            '鸡肉冻干宠物零食，适合作为奖励零食。',
            (SELECT id FROM d2c_product_categories WHERE code = 'treats'),
            'active',
            TRUE
          ),
          (
            'pet-cat-toy-feather-001',
            '羽毛逗猫棒',
            '互动逗猫玩具',
            '互动逗猫玩具，适合新手养猫家庭。',
            (SELECT id FROM d2c_product_categories WHERE code = 'toys'),
            'active',
            TRUE
          ),
          (
            'pet-care-wipes-001',
            '宠物清洁湿巾 80片',
            '日常清洁湿巾',
            '宠物日常清洁湿巾，适合外出和居家护理。',
            (SELECT id FROM d2c_product_categories WHERE code = 'care'),
            'active',
            TRUE
          ),
          (
            'pet-travel-bowl-001',
            '便携折叠食盆',
            '出行便携食盆',
            '适合外出携带的宠物折叠食盆。',
            (SELECT id FROM d2c_product_categories WHERE code = 'daily_travel'),
            'active',
            TRUE
          )
        """
    )

    op.execute(
        """
        INSERT INTO d2c_product_skus (
          product_id, sku_code, name, price_cents, currency, stock_status, sort_order
        )
        VALUES
          (
            (SELECT id FROM d2c_products WHERE product_code = 'pet-cat-food-salmon-001'),
            'CAT-FOOD-SALMON-1KG',
            '三文鱼成猫粮 1kg',
            1899,
            'USD',
            'in_stock',
            10
          ),
          (
            (SELECT id FROM d2c_products WHERE product_code = 'pet-cat-litter-tofu-001'),
            'CAT-LITTER-TOFU-6L',
            '豆腐猫砂 6L',
            1299,
            'USD',
            'in_stock',
            10
          ),
          (
            (SELECT id FROM d2c_products WHERE product_code = 'pet-cat-treat-chicken-001'),
            'CAT-TREAT-CHICKEN-80G',
            '鸡肉冻干零食 80g',
            999,
            'USD',
            'low_stock',
            10
          ),
          (
            (SELECT id FROM d2c_products WHERE product_code = 'pet-cat-toy-feather-001'),
            'CAT-TOY-FEATHER',
            '羽毛逗猫棒',
            699,
            'USD',
            'in_stock',
            10
          ),
          (
            (SELECT id FROM d2c_products WHERE product_code = 'pet-care-wipes-001'),
            'PET-CARE-WIPES-80',
            '宠物清洁湿巾 80片',
            799,
            'USD',
            'in_stock',
            10
          ),
          (
            (SELECT id FROM d2c_products WHERE product_code = 'pet-travel-bowl-001'),
            'PET-TRAVEL-BOWL',
            '便携折叠食盆',
            599,
            'USD',
            'out_of_stock',
            10
          )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_product_skus_sku_code", table_name="d2c_product_skus")
    op.drop_index("ix_d2c_product_skus_product_id", table_name="d2c_product_skus")
    op.drop_table("d2c_product_skus")

    op.drop_index("ix_d2c_products_product_code", table_name="d2c_products")
    op.drop_index("ix_d2c_products_category_id", table_name="d2c_products")
    op.drop_table("d2c_products")

    op.drop_index("ix_d2c_product_categories_code", table_name="d2c_product_categories")
    op.drop_table("d2c_product_categories")
