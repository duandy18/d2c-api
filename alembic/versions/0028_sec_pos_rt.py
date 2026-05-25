"""add_storefront_section_position_runtime_snapshots.

Revision ID: 0028_sec_pos_rt
Revises: 0027_storefront_sections_rt
Create Date: 2026-05-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0028_sec_pos_rt"
down_revision: str | Sequence[str] | None = "0027_storefront_sections_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "d2c_published_storefront_section_positions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("section_code", sa.String(length=96), nullable=False),
        sa.Column("position_code", sa.String(length=120), nullable=False),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("position_type", sa.String(length=32), nullable=False),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_position_id", sa.BigInteger(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "publish_version",
            "position_code",
            name="uq_d2c_pub_sec_pos_code",
        ),
    )
    op.create_index(
        "ix_d2c_pub_sec_pos_section",
        "d2c_published_storefront_section_positions",
        ["publish_version", "section_code", "sort_order"],
    )
    op.create_index(
        "ix_d2c_pub_sec_pos_offer",
        "d2c_published_storefront_section_positions",
        ["publish_version", "offer_code"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_d2c_pub_sec_pos_offer",
        table_name="d2c_published_storefront_section_positions",
    )
    op.drop_index(
        "ix_d2c_pub_sec_pos_section",
        table_name="d2c_published_storefront_section_positions",
    )
    op.drop_table("d2c_published_storefront_section_positions")
