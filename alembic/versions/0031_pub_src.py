"""set published sync source default to d2c-api

Revision ID: 0031_pub_src
Revises: 0030_site_config
Create Date: 2026-05-29 01:25:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0031_pub_src"
down_revision: str | Sequence[str] | None = "0030_site_config"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "d2c_publish_sync_runs",
        "source_service",
        existing_type=sa.String(length=64),
        server_default="d2c-api",
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "d2c_publish_sync_runs",
        "source_service",
        existing_type=sa.String(length=64),
        server_default="d2c-backoffice-api",
        existing_nullable=False,
    )
