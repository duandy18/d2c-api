from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_legacy_published_catalog_and_promotions_tables_are_retired() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_published_products" not in table_names
        assert "d2c_published_skus" not in table_names
        assert "d2c_published_prices" not in table_names
        assert "d2c_published_promotions" not in table_names
        assert "d2c_published_coupons" in table_names
        assert "d2c_publish_sync_runs" in table_names
    finally:
        engine.dispose()


def test_published_coupon_runtime_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        coupon_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_coupons")
        }
        sync_run_columns = {
            column["name"] for column in inspector.get_columns("d2c_publish_sync_runs")
        }

        assert {
            "publish_version",
            "coupon_code",
            "coupon_name",
            "promotion_code",
            "coupon_type",
            "total_limit",
            "per_customer_limit",
            "is_active",
            "raw_payload",
        }.issubset(coupon_columns)

        assert {
            "sync_scope",
            "source_service",
            "source_base_url",
            "source_endpoint",
            "publish_version",
            "status",
            "rows_fetched",
            "rows_upserted",
            "rows_deleted",
            "raw_summary",
        }.issubset(sync_run_columns)
    finally:
        engine.dispose()


def test_published_coupon_runtime_constraints_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        coupon_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_published_coupons")
        }

        assert "uq_d2c_published_coupons_version_code" in coupon_unique
    finally:
        engine.dispose()
