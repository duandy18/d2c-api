from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect, text

from app.models.order import D2COrder, D2COrderLine


def _database_url() -> str:
    url = (
        os.getenv("D2C_TEST_DATABASE_URL")
        or os.getenv("D2C_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c"
    )
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


def test_order_models_are_bound_to_expected_tables() -> None:
    assert D2COrder.__tablename__ == "d2c_orders"
    assert D2COrderLine.__tablename__ == "d2c_order_lines"

    order_columns = set(D2COrder.__table__.columns.keys())
    assert {
        "id",
        "order_no",
        "customer_id",
        "cart_id",
        "status",
        "currency",
        "item_count",
        "subtotal_cents",
        "recipient_name",
        "recipient_phone",
        "shipping_country",
        "shipping_province",
        "shipping_city",
        "shipping_district",
        "shipping_address_line1",
        "shipping_address_line2",
        "shipping_postal_code",
        "created_at",
        "updated_at",
    }.issubset(order_columns)

    line_columns = set(D2COrderLine.__table__.columns.keys())
    assert {
        "id",
        "order_id",
        "product_id",
        "sku_id",
        "product_code",
        "sku_code",
        "product_name",
        "sku_name",
        "quantity",
        "unit_price_cents",
        "line_subtotal_cents",
        "created_at",
    }.issubset(line_columns)


def test_order_owner_tables_exist_in_database() -> None:
    engine = create_engine(_database_url())
    try:
        inspector = inspect(engine)

        assert "d2c_orders" in inspector.get_table_names()
        assert "d2c_order_lines" in inspector.get_table_names()

        order_columns = {column["name"] for column in inspector.get_columns("d2c_orders")}
        assert {
            "order_no",
            "customer_id",
            "cart_id",
            "status",
            "currency",
            "item_count",
            "subtotal_cents",
            "recipient_name",
            "recipient_phone",
            "shipping_address_line1",
            "created_at",
            "updated_at",
        }.issubset(order_columns)

        line_columns = {column["name"] for column in inspector.get_columns("d2c_order_lines")}
        assert {
            "order_id",
            "product_id",
            "sku_id",
            "product_code",
            "sku_code",
            "product_name",
            "sku_name",
            "quantity",
            "unit_price_cents",
            "line_subtotal_cents",
            "created_at",
        }.issubset(line_columns)

        order_fk_targets = {fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_orders")}
        assert {"d2c_customers", "d2c_carts"}.issubset(order_fk_targets)

        line_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_order_lines")
        }
        assert {"d2c_orders", "d2c_products", "d2c_product_skus"}.issubset(line_fk_targets)

        with engine.connect() as connection:
            order_indexes = (
                connection.execute(
                    text(
                        """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = 'd2c_orders'
                    """
                    )
                )
                .scalars()
                .all()
            )
            assert "uq_d2c_orders_order_no" in order_indexes

            line_indexes = (
                connection.execute(
                    text(
                        """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = 'd2c_order_lines'
                    """
                    )
                )
                .scalars()
                .all()
            )
            assert "ix_d2c_order_lines_order_id" in line_indexes
    finally:
        engine.dispose()
