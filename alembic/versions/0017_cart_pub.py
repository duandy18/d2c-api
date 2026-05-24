"""switch cart and checkout item snapshots to published model.

Revision ID: 0017_cart_pub
Revises: 0016_publish_rt
Create Date: 2026-05-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_cart_pub"
down_revision: str | Sequence[str] | None = "0016_publish_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "d2c_cart_lines",
        sa.Column("publish_version", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "d2c_cart_lines",
        sa.Column("product_code", sa.String(length=96), nullable=True),
    )
    op.add_column(
        "d2c_cart_lines",
        sa.Column("sku_code", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "d2c_cart_lines",
        sa.Column("product_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "d2c_cart_lines",
        sa.Column("sku_name", sa.String(length=255), nullable=True),
    )

    op.execute(
        """
        UPDATE d2c_cart_lines cl
        SET
          publish_version = 'legacy-migrated',
          product_code = p.product_code,
          sku_code = s.sku_code,
          product_name = p.name,
          sku_name = s.name
        FROM d2c_products p, d2c_product_skus s
        WHERE cl.product_id = p.id
          AND cl.sku_id = s.id
        """
    )

    op.alter_column(
        "d2c_cart_lines",
        "publish_version",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.alter_column(
        "d2c_cart_lines",
        "product_code",
        existing_type=sa.String(length=96),
        nullable=False,
    )
    op.alter_column(
        "d2c_cart_lines",
        "sku_code",
        existing_type=sa.String(length=128),
        nullable=False,
    )
    op.alter_column(
        "d2c_cart_lines",
        "product_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "d2c_cart_lines",
        "sku_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.drop_constraint(
        "uq_d2c_cart_lines_cart_id_sku_id",
        "d2c_cart_lines",
        type_="unique",
    )
    op.drop_constraint(
        "fk_d2c_cart_lines_product_id",
        "d2c_cart_lines",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_d2c_cart_lines_sku_id",
        "d2c_cart_lines",
        type_="foreignkey",
    )
    op.drop_index("ix_d2c_cart_lines_product_id", table_name="d2c_cart_lines")
    op.drop_index("ix_d2c_cart_lines_sku_id", table_name="d2c_cart_lines")

    op.alter_column(
        "d2c_cart_lines",
        "product_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.alter_column(
        "d2c_cart_lines",
        "sku_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )

    op.create_unique_constraint(
        "uq_d2c_cart_lines_cart_id_publish_version_sku_code",
        "d2c_cart_lines",
        ["cart_id", "publish_version", "sku_code"],
    )
    op.create_index(
        "ix_d2c_cart_lines_publish_version",
        "d2c_cart_lines",
        ["publish_version"],
    )
    op.create_index(
        "ix_d2c_cart_lines_product_code",
        "d2c_cart_lines",
        ["product_code"],
    )
    op.create_index(
        "ix_d2c_cart_lines_sku_code",
        "d2c_cart_lines",
        ["sku_code"],
    )

    op.add_column(
        "d2c_order_lines",
        sa.Column("publish_version", sa.String(length=64), nullable=True),
    )
    op.execute(
        """
        UPDATE d2c_order_lines
        SET publish_version = 'legacy-migrated'
        WHERE publish_version IS NULL
        """
    )
    op.alter_column(
        "d2c_order_lines",
        "publish_version",
        existing_type=sa.String(length=64),
        nullable=False,
    )

    op.drop_constraint(
        "fk_d2c_order_lines_product_id",
        "d2c_order_lines",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_d2c_order_lines_sku_id",
        "d2c_order_lines",
        type_="foreignkey",
    )
    op.drop_index("ix_d2c_order_lines_product_id", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_sku_id", table_name="d2c_order_lines")

    op.alter_column(
        "d2c_order_lines",
        "product_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "d2c_order_lines",
        "sku_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "d2c_order_lines",
        "product_code",
        existing_type=sa.String(length=64),
        type_=sa.String(length=96),
        nullable=False,
    )
    op.alter_column(
        "d2c_order_lines",
        "sku_code",
        existing_type=sa.String(length=64),
        type_=sa.String(length=128),
        nullable=False,
    )

    op.create_index(
        "ix_d2c_order_lines_publish_version",
        "d2c_order_lines",
        ["publish_version"],
    )
    op.create_index(
        "ix_d2c_order_lines_product_code",
        "d2c_order_lines",
        ["product_code"],
    )
    op.create_index(
        "ix_d2c_order_lines_sku_code",
        "d2c_order_lines",
        ["sku_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_order_lines_sku_code", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_product_code", table_name="d2c_order_lines")
    op.drop_index("ix_d2c_order_lines_publish_version", table_name="d2c_order_lines")

    op.execute(
        """
        DELETE FROM d2c_order_lines
        WHERE product_id IS NULL
           OR sku_id IS NULL
        """
    )

    op.alter_column(
        "d2c_order_lines",
        "sku_code",
        existing_type=sa.String(length=128),
        type_=sa.String(length=64),
        nullable=False,
    )
    op.alter_column(
        "d2c_order_lines",
        "product_code",
        existing_type=sa.String(length=96),
        type_=sa.String(length=64),
        nullable=False,
    )
    op.alter_column(
        "d2c_order_lines",
        "sku_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "d2c_order_lines",
        "product_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_d2c_order_lines_sku_id",
        "d2c_order_lines",
        "d2c_product_skus",
        ["sku_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_d2c_order_lines_product_id",
        "d2c_order_lines",
        "d2c_products",
        ["product_id"],
        ["id"],
    )
    op.create_index(
        "ix_d2c_order_lines_sku_id",
        "d2c_order_lines",
        ["sku_id"],
    )
    op.create_index(
        "ix_d2c_order_lines_product_id",
        "d2c_order_lines",
        ["product_id"],
    )
    op.drop_column("d2c_order_lines", "publish_version")

    op.drop_index("ix_d2c_cart_lines_sku_code", table_name="d2c_cart_lines")
    op.drop_index("ix_d2c_cart_lines_product_code", table_name="d2c_cart_lines")
    op.drop_index("ix_d2c_cart_lines_publish_version", table_name="d2c_cart_lines")
    op.drop_constraint(
        "uq_d2c_cart_lines_cart_id_publish_version_sku_code",
        "d2c_cart_lines",
        type_="unique",
    )

    op.execute(
        """
        DELETE FROM d2c_cart_lines
        WHERE product_id IS NULL
           OR sku_id IS NULL
        """
    )

    op.alter_column(
        "d2c_cart_lines",
        "sku_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "d2c_cart_lines",
        "product_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )

    op.create_foreign_key(
        "fk_d2c_cart_lines_sku_id",
        "d2c_cart_lines",
        "d2c_product_skus",
        ["sku_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_d2c_cart_lines_product_id",
        "d2c_cart_lines",
        "d2c_products",
        ["product_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_d2c_cart_lines_cart_id_sku_id",
        "d2c_cart_lines",
        ["cart_id", "sku_id"],
    )
    op.create_index(
        "ix_d2c_cart_lines_sku_id",
        "d2c_cart_lines",
        ["sku_id"],
    )
    op.create_index(
        "ix_d2c_cart_lines_product_id",
        "d2c_cart_lines",
        ["product_id"],
    )

    op.drop_column("d2c_cart_lines", "sku_name")
    op.drop_column("d2c_cart_lines", "product_name")
    op.drop_column("d2c_cart_lines", "sku_code")
    op.drop_column("d2c_cart_lines", "product_code")
    op.drop_column("d2c_cart_lines", "publish_version")
