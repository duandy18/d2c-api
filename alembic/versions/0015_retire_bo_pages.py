"""retire_backoffice_page_registry

Revision ID: 0015_retire_bo_pages
Revises: 0014_backoffice_page_registry
Create Date: 2026-05-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_retire_bo_pages"
down_revision: str | Sequence[str] | None = "0014_backoffice_page_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop legacy backoffice page registry from d2c-api.

    Page registry ownership has moved to d2c-backoffice-api / d2c_backoffice_db.
    """

    op.drop_index("ix_d2c_backoffice_pages_sort_order", table_name="d2c_backoffice_pages")
    op.drop_index("ix_d2c_backoffice_pages_route_path", table_name="d2c_backoffice_pages")
    op.drop_index("ix_d2c_backoffice_pages_parent_code", table_name="d2c_backoffice_pages")
    op.drop_table("d2c_backoffice_pages")


def downgrade() -> None:
    """Recreate legacy table structure without restoring retired seed data."""

    op.create_table(
        "d2c_backoffice_pages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("page_code", sa.String(length=160), nullable=False),
        sa.Column("parent_code", sa.String(length=160), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("route_path", sa.String(length=240), nullable=False),
        sa.Column("component_key", sa.String(length=160), nullable=False),
        sa.Column("icon", sa.String(length=80), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "implementation_status",
            sa.String(length=32),
            nullable=False,
            server_default="planned",
        ),
        sa.Column(
            "data_status",
            sa.String(length=32),
            nullable=False,
            server_default="placeholder",
        ),
        sa.Column("required_permission", sa.String(length=160), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("page_code", name="uq_d2c_backoffice_pages_page_code"),
    )
    op.create_index(
        "ix_d2c_backoffice_pages_parent_code",
        "d2c_backoffice_pages",
        ["parent_code"],
    )
    op.create_index(
        "ix_d2c_backoffice_pages_route_path",
        "d2c_backoffice_pages",
        ["route_path"],
    )
    op.create_index(
        "ix_d2c_backoffice_pages_sort_order",
        "d2c_backoffice_pages",
        ["sort_order"],
    )
