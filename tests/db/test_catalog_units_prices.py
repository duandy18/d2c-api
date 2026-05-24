from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine

RETIRED_TABLES = {
    "d2c_products",
    "d2c_product_skus",
    "d2c_product_categories",
    "d2c_units",
    "d2c_price_lists",
    "d2c_sku_prices",
}


def test_legacy_catalog_owner_tables_are_retired_from_database() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert RETIRED_TABLES.isdisjoint(table_names)
    finally:
        engine.dispose()


def test_published_catalog_runtime_tables_remain_available() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_published_products" in table_names
        assert "d2c_published_skus" in table_names
        assert "d2c_published_prices" in table_names
    finally:
        engine.dispose()
