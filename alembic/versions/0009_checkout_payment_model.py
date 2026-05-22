"""add_checkout_payment_model.

Revision ID: 0009_checkout_payment_model
Revises: 0008_cart_summary_fields
Create Date: 2026-05-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_checkout_payment_model"
down_revision: str | Sequence[str] | None = "0008_cart_summary_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "d2c_orders",
        sa.Column("cart_code", sa.String(length=96), nullable=True),
    )
    op.add_column(
        "d2c_orders",
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        """
        UPDATE d2c_orders o
        SET cart_code = c.cart_code
        FROM d2c_carts c
        WHERE o.cart_id = c.id
          AND o.cart_code IS NULL
        """
    )

    op.alter_column(
        "d2c_orders",
        "cart_code",
        existing_type=sa.String(length=96),
        nullable=False,
    )
    op.create_index(
        "ix_d2c_orders_cart_code",
        "d2c_orders",
        ["cart_code"],
        unique=False,
    )

    op.create_table(
        "d2c_payments",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("payment_no", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="mock"),
        sa.Column(
            "payment_method",
            sa.String(length=64),
            nullable=False,
            server_default="mock",
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("provider_payment_id", sa.String(length=128), nullable=True),
        sa.Column("provider_trade_no", sa.String(length=128), nullable=True),
        sa.Column("payment_reference", sa.String(length=128), nullable=True),
        sa.Column("notify_payload", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
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
            "amount_cents >= 0",
            name="ck_d2c_payments_amount_cents_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_payments_customer_id",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["d2c_orders.id"],
            name="fk_d2c_payments_order_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_no", name="uq_d2c_payments_payment_no"),
    )
    op.create_index(
        "ix_d2c_payments_customer_id",
        "d2c_payments",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_payments_order_id",
        "d2c_payments",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_payments_order_no",
        "d2c_payments",
        ["order_no"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_payments_payment_no",
        "d2c_payments",
        ["payment_no"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_payments_provider",
        "d2c_payments",
        ["provider"],
        unique=False,
    )
    op.create_index(
        "ix_d2c_payments_status",
        "d2c_payments",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_d2c_payments_status", table_name="d2c_payments")
    op.drop_index("ix_d2c_payments_provider", table_name="d2c_payments")
    op.drop_index("ix_d2c_payments_payment_no", table_name="d2c_payments")
    op.drop_index("ix_d2c_payments_order_no", table_name="d2c_payments")
    op.drop_index("ix_d2c_payments_order_id", table_name="d2c_payments")
    op.drop_index("ix_d2c_payments_customer_id", table_name="d2c_payments")
    op.drop_table("d2c_payments")

    op.drop_index("ix_d2c_orders_cart_code", table_name="d2c_orders")
    op.drop_column("d2c_orders", "paid_at")
    op.drop_column("d2c_orders", "cart_code")
