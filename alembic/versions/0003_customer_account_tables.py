"""customer account tables

Revision ID: 0003_customer_account_tables
Revises: 0002_catalog_owner_tables
Create Date: 2026-05-22

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_customer_account_tables"
down_revision: str | Sequence[str] | None = "0002_catalog_owner_tables"
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
        "d2c_customers",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("customer_code", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        timestamp_column("registered_at"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.UniqueConstraint("customer_code", name="uq_d2c_customers_customer_code"),
        sa.UniqueConstraint("email", name="uq_d2c_customers_email"),
        sa.UniqueConstraint("phone", name="uq_d2c_customers_phone"),
    )
    op.create_index("ix_d2c_customers_customer_code", "d2c_customers", ["customer_code"])
    op.create_index("ix_d2c_customers_email", "d2c_customers", ["email"])
    op.create_index("ix_d2c_customers_phone", "d2c_customers", ["phone"])

    op.create_table(
        "d2c_customer_password_credentials",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        timestamp_column("password_updated_at"),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_customer_password_credentials_customer_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "customer_id",
            name="uq_d2c_customer_password_credentials_customer_id",
        ),
    )
    op.create_index(
        "ix_d2c_customer_password_credentials_customer_id",
        "d2c_customer_password_credentials",
        ["customer_id"],
    )

    op.create_table(
        "d2c_customer_addresses",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("recipient_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False, server_default="US"),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("address_line1", sa.String(length=240), nullable=False),
        sa.Column("address_line2", sa.String(length=240), nullable=True),
        sa.Column("postal_code", sa.String(length=32), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_customer_addresses_customer_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_d2c_customer_addresses_customer_id",
        "d2c_customer_addresses",
        ["customer_id"],
    )

    op.create_table(
        "d2c_customer_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("session_token_hash", sa.String(length=128), nullable=False),
        timestamp_column("issued_at"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        timestamp_column("created_at"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["d2c_customers.id"],
            name="fk_d2c_customer_sessions_customer_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "session_token_hash",
            name="uq_d2c_customer_sessions_token_hash",
        ),
    )
    op.create_index(
        "ix_d2c_customer_sessions_customer_id",
        "d2c_customer_sessions",
        ["customer_id"],
    )
    op.create_index(
        "ix_d2c_customer_sessions_token_hash",
        "d2c_customer_sessions",
        ["session_token_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_customer_sessions_token_hash", table_name="d2c_customer_sessions")
    op.drop_index("ix_d2c_customer_sessions_customer_id", table_name="d2c_customer_sessions")
    op.drop_table("d2c_customer_sessions")

    op.drop_index("ix_d2c_customer_addresses_customer_id", table_name="d2c_customer_addresses")
    op.drop_table("d2c_customer_addresses")

    op.drop_index(
        "ix_d2c_customer_password_credentials_customer_id",
        table_name="d2c_customer_password_credentials",
    )
    op.drop_table("d2c_customer_password_credentials")

    op.drop_index("ix_d2c_customers_phone", table_name="d2c_customers")
    op.drop_index("ix_d2c_customers_email", table_name="d2c_customers")
    op.drop_index("ix_d2c_customers_customer_code", table_name="d2c_customers")
    op.drop_table("d2c_customers")
