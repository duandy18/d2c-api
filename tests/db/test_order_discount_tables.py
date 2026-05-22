from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_order_discount_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        order_columns = {column["name"] for column in inspector.get_columns("d2c_orders")}

        assert {
            "discount_cents",
            "payable_cents",
            "promotion_id",
            "promotion_code",
        }.issubset(order_columns)
    finally:
        engine.dispose()


def test_order_discount_constraints_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        check_names = {
            constraint["name"] for constraint in inspector.get_check_constraints("d2c_orders")
        }

        assert "ck_d2c_orders_discount_cents_non_negative" in check_names
        assert "ck_d2c_orders_payable_cents_non_negative" in check_names
        assert "ck_d2c_orders_discount_not_exceed_subtotal" in check_names
        assert "ck_d2c_orders_payable_matches_discount" in check_names

        fk_targets = {fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_orders")}
        assert "d2c_promotions" in fk_targets
    finally:
        engine.dispose()
