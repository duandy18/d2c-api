"""detach published coupons from legacy promotions.

Revision ID: 0022_pub_coupon_rt
Revises: 0021_pub_snapshot_rt
Create Date: 2026-05-25
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0022_pub_coupon_rt"
down_revision: str | Sequence[str] | None = "0021_pub_snapshot_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_d2c_published_coupons_promotion_version",
        "d2c_published_coupons",
        type_="foreignkey",
    )
    op.create_index(
        "ix_d2c_pub_coupons_rule",
        "d2c_published_coupons",
        ["publish_version", "promotion_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_d2c_pub_coupons_rule", table_name="d2c_published_coupons")
    op.create_foreign_key(
        "fk_d2c_published_coupons_promotion_version",
        "d2c_published_coupons",
        "d2c_published_promotions",
        ["publish_version", "promotion_code"],
        ["publish_version", "promotion_code"],
        ondelete="CASCADE",
    )
