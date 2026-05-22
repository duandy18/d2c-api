from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_order_coupon_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        order_columns = {column["name"] for column in inspector.get_columns("d2c_orders")}

        assert {"coupon_id", "coupon_code"}.issubset(order_columns)
    finally:
        engine.dispose()


def test_order_coupon_foreign_key_and_indexes_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("d2c_orders")}
        fk_targets = {fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_orders")}
        index_names = {index["name"] for index in inspector.get_indexes("d2c_orders")}

        assert "fk_d2c_orders_coupon_id" in fk_names
        assert "d2c_coupons" in fk_targets
        assert "ix_d2c_orders_coupon_id" in index_names
        assert "ix_d2c_orders_coupon_code" in index_names
    finally:
        engine.dispose()
