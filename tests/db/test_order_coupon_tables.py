from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_order_coupon_snapshot_columns_exist_without_legacy_coupon_id() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        order_columns = {column["name"] for column in inspector.get_columns("d2c_orders")}

        assert {
            "coupon_code",
            "coupon_name",
            "coupon_type",
            "coupon_publish_version",
        }.issubset(order_columns)
        assert "coupon_id" not in order_columns
    finally:
        engine.dispose()


def test_order_coupon_indexes_exist_without_legacy_coupon_fk() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("d2c_orders")}
        fk_targets = {fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_orders")}
        index_names = {index["name"] for index in inspector.get_indexes("d2c_orders")}

        assert "fk_d2c_orders_coupon_id" not in fk_names
        assert "d2c_coupons" not in fk_targets
        assert "ix_d2c_orders_coupon_id" not in index_names
        assert "ix_d2c_orders_coupon_code" in index_names
        assert "ix_d2c_orders_coupon_publish_version" in index_names
    finally:
        engine.dispose()
