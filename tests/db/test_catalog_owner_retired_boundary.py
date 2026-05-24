from app.core.orm import Base

RETIRED_TABLES = {
    "d2c_products",
    "d2c_product_skus",
    "d2c_product_categories",
    "d2c_units",
    "d2c_price_lists",
    "d2c_sku_prices",
}


def test_legacy_catalog_owner_tables_are_not_registered_in_current_orm_metadata() -> None:
    assert RETIRED_TABLES.isdisjoint(Base.metadata.tables)
