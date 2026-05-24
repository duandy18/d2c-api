from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect, text

from app.domains.orders.models.order import D2COrder, D2COrderLine


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
        "discount_cents",
        "payable_cents",
        "promotion_id",
        "promotion_code",
        "promotion_name",
        "promotion_type",
        "promotion_discount_type",
        "promotion_discount_value",
        "promotion_publish_version",
        "coupon_id",
        "coupon_code",
        "coupon_name",
        "coupon_type",
        "coupon_publish_version",
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
        "publish_version",
        "product_code",
        "sku_code",
        "product_name",
        "sku_name",
        "pms_item_id",
        "pms_sku",
        "category_code",
        "category_name",
        "brand_code",
        "brand_name",
        "sales_unit_code",
        "sales_unit_name",
        "barcode",
        "spec_text",
        "price_list_code",
        "compare_at_price_cents",
        "source_product_id",
        "source_sku_id",
        "source_price_id",
        "quantity",
        "unit_price_cents",
        "line_subtotal_cents",
        "created_at",
    }.issubset(line_columns)

    assert D2COrderLine.__table__.columns["product_id"].nullable is True
    assert D2COrderLine.__table__.columns["sku_id"].nullable is True


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
            "promotion_name",
            "promotion_type",
            "promotion_discount_type",
            "promotion_discount_value",
            "promotion_publish_version",
            "coupon_name",
            "coupon_type",
            "coupon_publish_version",
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
            "publish_version",
            "product_code",
            "sku_code",
            "product_name",
            "sku_name",
            "pms_item_id",
            "pms_sku",
            "category_code",
            "category_name",
            "brand_code",
            "brand_name",
            "sales_unit_code",
            "sales_unit_name",
            "barcode",
            "spec_text",
            "price_list_code",
            "compare_at_price_cents",
            "source_product_id",
            "source_sku_id",
            "source_price_id",
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
        assert line_fk_targets == {"d2c_orders"}

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
            assert "ix_d2c_orders_promotion_publish_version" in order_indexes
            assert "ix_d2c_orders_coupon_publish_version" in order_indexes

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
            assert "ix_d2c_order_lines_publish_version" in line_indexes
            assert "ix_d2c_order_lines_product_code" in line_indexes
            assert "ix_d2c_order_lines_sku_code" in line_indexes
            assert "ix_d2c_order_lines_category_code" in line_indexes
            assert "ix_d2c_order_lines_brand_code" in line_indexes
            assert "ix_d2c_order_lines_price_list_code" in line_indexes
    finally:
        engine.dispose()
