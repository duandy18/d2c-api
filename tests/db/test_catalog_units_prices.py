from sqlalchemy import inspect, text

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_catalog_unit_and_price_tables_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_units" in table_names
        assert "d2c_price_lists" in table_names
        assert "d2c_sku_prices" in table_names
    finally:
        engine.dispose()


def test_catalog_unit_and_price_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        unit_columns = {column["name"] for column in inspector.get_columns("d2c_units")}
        sku_columns = {column["name"] for column in inspector.get_columns("d2c_product_skus")}
        price_list_columns = {column["name"] for column in inspector.get_columns("d2c_price_lists")}
        sku_price_columns = {column["name"] for column in inspector.get_columns("d2c_sku_prices")}

        assert {
            "id",
            "unit_code",
            "name",
            "unit_type",
            "symbol",
            "precision",
            "is_base_unit",
            "base_unit_code",
            "conversion_factor",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        }.issubset(unit_columns)

        assert {
            "sales_unit_id",
            "package_quantity",
            "package_unit_text",
        }.issubset(sku_columns)

        assert {
            "id",
            "price_list_code",
            "name",
            "currency",
            "region_code",
            "channel",
            "customer_segment",
            "priority",
            "is_default",
            "is_active",
            "effective_from",
            "effective_to",
            "created_at",
            "updated_at",
        }.issubset(price_list_columns)

        assert {
            "id",
            "price_list_id",
            "sku_id",
            "price_cents",
            "compare_at_price_cents",
            "currency",
            "effective_from",
            "effective_to",
            "is_active",
            "created_at",
            "updated_at",
        }.issubset(sku_price_columns)
    finally:
        engine.dispose()


def test_catalog_unit_and_price_constraints_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        unit_unique_names = {
            constraint["name"] for constraint in inspector.get_unique_constraints("d2c_units")
        }
        price_list_unique_names = {
            constraint["name"] for constraint in inspector.get_unique_constraints("d2c_price_lists")
        }
        sku_price_unique_names = {
            constraint["name"] for constraint in inspector.get_unique_constraints("d2c_sku_prices")
        }

        assert "uq_d2c_units_unit_code" in unit_unique_names
        assert "uq_d2c_price_lists_code" in price_list_unique_names
        assert "uq_d2c_sku_prices_price_list_id_sku_id" in sku_price_unique_names

        sku_foreign_key_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_product_skus")
        }
        sku_price_foreign_key_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_sku_prices")
        }

        assert "d2c_units" in sku_foreign_key_targets
        assert {"d2c_price_lists", "d2c_product_skus"}.issubset(sku_price_foreign_key_targets)
    finally:
        engine.dispose()


def test_catalog_units_and_default_prices_are_seeded() -> None:
    engine = create_db_engine(load_settings())
    try:
        with engine.connect() as connection:
            unit_codes = set(
                connection.execute(
                    text(
                        """
                        SELECT unit_code
                        FROM d2c_units
                        WHERE is_active IS TRUE
                        """
                    )
                )
                .scalars()
                .all()
            )

            assert {
                "piece",
                "sheet",
                "pack",
                "bag",
                "g",
                "kg",
                "ml",
                "l",
            }.issubset(unit_codes)

            default_price_list = (
                connection.execute(
                    text(
                        """
                        SELECT price_list_code, currency, channel, customer_segment, is_default
                        FROM d2c_price_lists
                        WHERE price_list_code = 'default_usd_storefront'
                        """
                    )
                )
                .mappings()
                .one()
            )

            assert default_price_list["currency"] == "USD"
            assert default_price_list["channel"] == "storefront"
            assert default_price_list["customer_segment"] == "default"
            assert default_price_list["is_default"] is True

            sku_count = connection.execute(
                text("SELECT COUNT(*) FROM d2c_product_skus")
            ).scalar_one()
            sku_price_count = connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM d2c_sku_prices sp
                    JOIN d2c_price_lists pl ON pl.id = sp.price_list_id
                    WHERE pl.price_list_code = 'default_usd_storefront'
                    """
                )
            ).scalar_one()

            assert sku_price_count == sku_count
    finally:
        engine.dispose()


def test_sku_units_and_default_prices_are_backfilled() -> None:
    engine = create_db_engine(load_settings())
    try:
        with engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        SELECT
                          s.sku_code,
                          u.unit_code,
                          s.package_quantity,
                          s.package_unit_text,
                          s.price_cents AS legacy_price_cents,
                          sp.price_cents AS default_price_cents,
                          sp.currency
                        FROM d2c_product_skus s
                        JOIN d2c_units u ON u.id = s.sales_unit_id
                        JOIN d2c_sku_prices sp ON sp.sku_id = s.id
                        JOIN d2c_price_lists pl ON pl.id = sp.price_list_id
                        WHERE pl.price_list_code = 'default_usd_storefront'
                        ORDER BY s.id
                        """
                    )
                )
                .mappings()
                .all()
            )

            assert rows
            assert all(row["package_quantity"] > 0 for row in rows)
            assert all(row["package_unit_text"] for row in rows)
            assert all(row["legacy_price_cents"] == row["default_price_cents"] for row in rows)
            assert {row["currency"] for row in rows} == {"USD"}

            unit_by_sku = {row["sku_code"]: row["unit_code"] for row in rows}
            assert unit_by_sku["CAT-FOOD-SALMON-1KG"] == "bag"
            assert unit_by_sku["PET-CARE-WIPES-80"] == "pack"
            assert unit_by_sku["PET-TRAVEL-BOWL"] == "piece"
    finally:
        engine.dispose()
