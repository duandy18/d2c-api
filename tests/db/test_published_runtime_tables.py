from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_published_runtime_tables_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_published_products" in table_names
        assert "d2c_published_skus" in table_names
        assert "d2c_published_prices" in table_names
        assert "d2c_published_promotions" in table_names
        assert "d2c_published_coupons" in table_names
        assert "d2c_publish_sync_runs" in table_names
    finally:
        engine.dispose()


def test_published_catalog_runtime_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        product_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_products")
        }
        sku_columns = {column["name"] for column in inspector.get_columns("d2c_published_skus")}
        price_columns = {column["name"] for column in inspector.get_columns("d2c_published_prices")}

        assert {
            "publish_version",
            "pms_item_id",
            "pms_sku",
            "product_code",
            "product_name",
            "display_name",
            "category_code",
            "category_name",
            "brand_code",
            "brand_name",
            "display_status",
            "sell_status",
            "raw_payload",
        }.issubset(product_columns)

        assert {
            "publish_version",
            "product_code",
            "sku_code",
            "sku_name",
            "display_sku_name",
            "sales_unit_code",
            "sales_unit_name",
            "barcode",
            "is_sellable",
            "raw_payload",
        }.issubset(sku_columns)

        assert {
            "publish_version",
            "price_list_code",
            "channel",
            "sku_code",
            "currency",
            "price_cents",
            "compare_at_price_cents",
            "effective_from",
            "effective_until",
            "is_active",
            "priority",
            "raw_payload",
        }.issubset(price_columns)
    finally:
        engine.dispose()


def test_published_marketing_runtime_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        promotion_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_promotions")
        }
        coupon_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_coupons")
        }
        sync_run_columns = {
            column["name"] for column in inspector.get_columns("d2c_publish_sync_runs")
        }

        assert {
            "publish_version",
            "promotion_code",
            "promotion_name",
            "promotion_type",
            "discount_type",
            "discount_value",
            "scope_type",
            "min_order_amount_cents",
            "max_discount_cents",
            "currency",
            "priority",
            "stackable",
            "is_active",
            "raw_payload",
        }.issubset(promotion_columns)

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


def test_published_runtime_constraints_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        product_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_published_products")
        }
        sku_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_published_skus")
        }
        price_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_published_prices")
        }
        promotion_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_published_promotions")
        }
        coupon_unique = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_published_coupons")
        }

        assert "uq_d2c_published_products_version_product" in product_unique
        assert "uq_d2c_published_skus_version_sku" in sku_unique
        assert "uq_d2c_published_prices_version_list_channel_sku" in price_unique
        assert "uq_d2c_published_promotions_version_code" in promotion_unique
        assert "uq_d2c_published_coupons_version_code" in coupon_unique
    finally:
        engine.dispose()
