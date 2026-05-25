"""add client presentation runtime snapshot tables

Revision ID: 0029_client_pres_rt
Revises: 0028_sec_pos_rt
Create Date: 2026-05-25

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0029_client_pres_rt"
down_revision: str | Sequence[str] | None = "0028_sec_pos_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "d2c_published_client_pages",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("page_code", sa.String(length=96), nullable=False),
        sa.Column("page_type", sa.String(length=32), nullable=False),
        sa.Column("route_path", sa.String(length=240), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(length=200), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("display_status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_page_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "page_code", name="uq_d2c_pub_cp_code"),
    )
    op.create_index(
        "ix_d2c_pub_cp_status",
        "d2c_published_client_pages",
        ["publish_version", "display_status", "is_active"],
    )

    op.create_table(
        "d2c_published_client_regions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("region_code", sa.String(length=96), nullable=False),
        sa.Column("page_code", sa.String(length=96), nullable=False),
        sa.Column("region_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("allowed_block_types", sa.JSON(), nullable=False),
        sa.Column("max_blocks", sa.Integer(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("display_status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_region_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "region_code", name="uq_d2c_pub_cr_code"),
    )
    op.create_index(
        "ix_d2c_pub_cr_page_sort",
        "d2c_published_client_regions",
        ["publish_version", "page_code", "sort_order"],
    )
    op.create_index(
        "ix_d2c_pub_cr_status",
        "d2c_published_client_regions",
        ["publish_version", "display_status", "is_active"],
    )

    op.create_table(
        "d2c_published_client_block_types",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("block_type", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("renderer_key", sa.String(length=120), nullable=False),
        sa.Column("allowed_region_types", sa.JSON(), nullable=False),
        sa.Column("allowed_content_types", sa.JSON(), nullable=False),
        sa.Column("layout_schema", sa.JSON(), nullable=True),
        sa.Column("slot_schema", sa.JSON(), nullable=True),
        sa.Column("action_schema", sa.JSON(), nullable=True),
        sa.Column("analytics_schema", sa.JSON(), nullable=True),
        sa.Column("data_contract_version", sa.String(length=32), nullable=False),
        sa.Column("display_status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_block_type_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "block_type", name="uq_d2c_pub_cbt_code"),
    )
    op.create_index(
        "ix_d2c_pub_cbt_status",
        "d2c_published_client_block_types",
        ["publish_version", "display_status", "is_active"],
    )

    op.create_table(
        "d2c_published_client_surfaces",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("surface_code", sa.String(length=64), nullable=False),
        sa.Column("surface_name", sa.String(length=120), nullable=False),
        sa.Column("surface_type", sa.String(length=32), nullable=False),
        sa.Column("device_family", sa.String(length=32), nullable=False),
        sa.Column("supported_renderer_keys", sa.JSON(), nullable=False),
        sa.Column("breakpoint_profile", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_surface_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "surface_code", name="uq_d2c_pub_cs_code"),
    )
    op.create_index(
        "ix_d2c_pub_cs_type",
        "d2c_published_client_surfaces",
        ["publish_version", "surface_type", "is_active"],
    )

    op.create_table(
        "d2c_published_client_data_bindings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("binding_code", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_code", sa.String(length=96), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("data_source_type", sa.String(length=64), nullable=False),
        sa.Column("data_source_ref", sa.String(length=120), nullable=False),
        sa.Column("query_params", sa.JSON(), nullable=True),
        sa.Column("sort_policy", sa.JSON(), nullable=True),
        sa.Column("result_limit", sa.Integer(), nullable=True),
        sa.Column("refresh_policy", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_binding_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "binding_code", name="uq_d2c_pub_cdb_code"),
    )
    op.create_index(
        "ix_d2c_pub_cdb_target",
        "d2c_published_client_data_bindings",
        ["publish_version", "target_type", "target_code"],
    )

    op.create_table(
        "d2c_published_client_visibility_rules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("rule_code", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_code", sa.String(length=96), nullable=False),
        sa.Column("client_surface_codes", sa.JSON(), nullable=False),
        sa.Column("customer_segments", sa.JSON(), nullable=False),
        sa.Column("login_state", sa.String(length=32), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rule_expression", sa.JSON(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_rule_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "rule_code", name="uq_d2c_pub_cvr_code"),
    )
    op.create_index(
        "ix_d2c_pub_cvr_target",
        "d2c_published_client_visibility_rules",
        ["publish_version", "target_type", "target_code"],
    )
    op.create_index(
        "ix_d2c_pub_cvr_active",
        "d2c_published_client_visibility_rules",
        ["publish_version", "is_active", "priority"],
    )

    op.create_table(
        "d2c_published_client_action_policies",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("policy_code", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_code", sa.String(length=96), nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=True),
        sa.Column("target_page_code", sa.String(length=96), nullable=True),
        sa.Column("target_ref", sa.String(length=120), nullable=True),
        sa.Column("open_mode", sa.String(length=32), nullable=False),
        sa.Column("action_payload", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_policy_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "policy_code", name="uq_d2c_pub_cap_code"),
    )
    op.create_index(
        "ix_d2c_pub_cap_target",
        "d2c_published_client_action_policies",
        ["publish_version", "target_type", "target_code"],
    )

    op.create_table(
        "d2c_published_client_tracking_policies",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("publish_version", sa.String(length=64), nullable=False),
        sa.Column("policy_code", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_code", sa.String(length=96), nullable=False),
        sa.Column("event_name", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_trigger", sa.String(length=32), nullable=False),
        sa.Column("tracking_params", sa.JSON(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_policy_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("publish_version", "policy_code", name="uq_d2c_pub_ctp_code"),
    )
    op.create_index(
        "ix_d2c_pub_ctp_target",
        "d2c_published_client_tracking_policies",
        ["publish_version", "target_type", "target_code"],
    )


def downgrade() -> None:
    op.drop_table("d2c_published_client_tracking_policies")
    op.drop_table("d2c_published_client_action_policies")
    op.drop_table("d2c_published_client_visibility_rules")
    op.drop_table("d2c_published_client_data_bindings")
    op.drop_table("d2c_published_client_surfaces")
    op.drop_table("d2c_published_client_block_types")
    op.drop_table("d2c_published_client_regions")
    op.drop_table("d2c_published_client_pages")
