from __future__ import annotations

from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_engine

CLIENT_PRESENTATION_TABLES = {
    "d2c_published_client_pages",
    "d2c_published_client_regions",
    "d2c_published_client_block_types",
    "d2c_published_client_surfaces",
    "d2c_published_client_data_bindings",
    "d2c_published_client_visibility_rules",
    "d2c_published_client_action_policies",
    "d2c_published_client_tracking_policies",
}


def test_client_presentation_runtime_tables_exist() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert CLIENT_PRESENTATION_TABLES.issubset(table_names)
    finally:
        engine.dispose()


def test_client_presentation_runtime_key_columns_exist() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)

        columns_by_table = {
            table: {column["name"] for column in inspector.get_columns(table)}
            for table in CLIENT_PRESENTATION_TABLES
        }

        assert {
            "publish_version",
            "page_code",
            "page_type",
            "route_path",
            "title",
            "display_status",
            "is_active",
        }.issubset(columns_by_table["d2c_published_client_pages"])
        assert {
            "publish_version",
            "region_code",
            "page_code",
            "region_type",
            "allowed_block_types",
            "max_blocks",
            "is_required",
        }.issubset(columns_by_table["d2c_published_client_regions"])
        assert {
            "publish_version",
            "block_type",
            "renderer_key",
            "allowed_region_types",
            "allowed_content_types",
            "layout_schema",
        }.issubset(columns_by_table["d2c_published_client_block_types"])
        assert {
            "publish_version",
            "surface_code",
            "surface_type",
            "device_family",
            "supported_renderer_keys",
        }.issubset(columns_by_table["d2c_published_client_surfaces"])
        assert {
            "publish_version",
            "binding_code",
            "target_type",
            "target_code",
            "data_source_type",
            "data_source_ref",
        }.issubset(columns_by_table["d2c_published_client_data_bindings"])
        assert {
            "publish_version",
            "rule_code",
            "target_type",
            "target_code",
            "client_surface_codes",
            "rule_expression",
        }.issubset(columns_by_table["d2c_published_client_visibility_rules"])
        assert {
            "publish_version",
            "policy_code",
            "target_type",
            "target_code",
            "action_type",
            "action_payload",
        }.issubset(columns_by_table["d2c_published_client_action_policies"])
        assert {
            "publish_version",
            "policy_code",
            "target_type",
            "target_code",
            "event_name",
            "tracking_params",
        }.issubset(columns_by_table["d2c_published_client_tracking_policies"])
    finally:
        engine.dispose()


def test_client_presentation_runtime_unique_constraints_and_indexes_exist() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)

        expected_unique_names = {
            "d2c_published_client_pages": "uq_d2c_pub_cp_code",
            "d2c_published_client_regions": "uq_d2c_pub_cr_code",
            "d2c_published_client_block_types": "uq_d2c_pub_cbt_code",
            "d2c_published_client_surfaces": "uq_d2c_pub_cs_code",
            "d2c_published_client_data_bindings": "uq_d2c_pub_cdb_code",
            "d2c_published_client_visibility_rules": "uq_d2c_pub_cvr_code",
            "d2c_published_client_action_policies": "uq_d2c_pub_cap_code",
            "d2c_published_client_tracking_policies": "uq_d2c_pub_ctp_code",
        }

        for table_name, constraint_name in expected_unique_names.items():
            unique_names = {
                constraint["name"] for constraint in inspector.get_unique_constraints(table_name)
            }
            index_names = {index["name"] for index in inspector.get_indexes(table_name)}

            assert constraint_name in unique_names
            assert index_names
    finally:
        engine.dispose()
