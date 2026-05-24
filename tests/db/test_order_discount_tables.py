from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_order_discount_columns_exist_without_legacy_promotion_id() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        order_columns = {column["name"] for column in inspector.get_columns("d2c_orders")}

        assert {
            "discount_cents",
            "payable_cents",
            "promotion_code",
            "promotion_name",
            "promotion_type",
            "promotion_discount_type",
            "promotion_discount_value",
            "promotion_publish_version",
        }.issubset(order_columns)
        assert "promotion_id" not in order_columns
    finally:
        engine.dispose()


def test_order_discount_constraints_exist_without_legacy_promotion_fk() -> None:
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
        index_names = {index["name"] for index in inspector.get_indexes("d2c_orders")}

        assert "d2c_promotions" not in fk_targets
        assert "ix_d2c_orders_promotion_id" not in index_names
    finally:
        engine.dispose()
