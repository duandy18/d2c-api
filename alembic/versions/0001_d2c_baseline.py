"""d2c baseline

Revision ID: 0001_d2c_baseline
Revises:
Create Date: 2026-05-22

"""
from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_d2c_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Baseline migration for D2C.

    This migration intentionally creates no business tables.
    """


def downgrade() -> None:
    """Downgrade baseline migration."""
