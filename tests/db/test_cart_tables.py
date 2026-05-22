from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_cart_tables_exist_after_migration() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        assert "d2c_carts" in inspector.get_table_names()
        assert "d2c_cart_lines" in inspector.get_table_names()
    finally:
        engine.dispose()


def test_cart_table_columns() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        cart_columns = {column["name"] for column in inspector.get_columns("d2c_carts")}
        cart_line_columns = {column["name"] for column in inspector.get_columns("d2c_cart_lines")}

        assert {
            "id",
            "cart_code",
            "customer_id",
            "anonymous_id",
            "session_code",
            "status",
            "currency",
            "line_count",
            "item_count",
            "subtotal_cents",
            "created_at",
            "updated_at",
        }.issubset(cart_columns)

        assert {
            "id",
            "cart_id",
            "product_id",
            "sku_id",
            "quantity",
            "unit_price_cents",
            "currency",
            "line_subtotal_cents",
            "created_at",
            "updated_at",
        }.issubset(cart_line_columns)
    finally:
        engine.dispose()


def test_cart_line_unique_constraint() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        unique_constraints = inspector.get_unique_constraints("d2c_cart_lines")
        unique_names = {constraint["name"] for constraint in unique_constraints}

        assert "uq_d2c_cart_lines_cart_id_sku_id" in unique_names
    finally:
        engine.dispose()


def test_cart_summary_constraints_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        check_constraints = inspector.get_check_constraints("d2c_carts")
        check_names = {constraint["name"] for constraint in check_constraints}

        assert "ck_d2c_carts_line_count_non_negative" in check_names
        assert "ck_d2c_carts_item_count_non_negative" in check_names
        assert "ck_d2c_carts_subtotal_cents_non_negative" in check_names
    finally:
        engine.dispose()
