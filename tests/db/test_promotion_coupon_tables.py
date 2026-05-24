from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_legacy_promotion_coupon_owner_tables_are_retired() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_promotions" not in table_names
        assert "d2c_promotion_targets" not in table_names
        assert "d2c_coupons" not in table_names
        assert "d2c_customer_coupons" in table_names
    finally:
        engine.dispose()


def test_customer_coupon_usage_fact_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        column_info = {
            column["name"]: column for column in inspector.get_columns("d2c_customer_coupons")
        }
        columns = set(column_info)

        assert {
            "id",
            "customer_coupon_code",
            "publish_version",
            "coupon_code",
            "coupon_name",
            "coupon_type",
            "promotion_code",
            "promotion_name",
            "promotion_type",
            "promotion_discount_type",
            "promotion_discount_value",
            "customer_id",
            "status",
            "claimed_at",
            "used_at",
            "order_id",
            "order_no",
            "created_at",
            "updated_at",
        }.issubset(columns)
        assert "coupon_id" not in columns
    finally:
        engine.dispose()


def test_customer_coupon_usage_fact_constraints_and_indexes_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        unique_names = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_customer_coupons")
        }
        check_names = {
            constraint["name"]
            for constraint in inspector.get_check_constraints("d2c_customer_coupons")
        }
        index_names = {
            index["name"] for index in inspector.get_indexes("d2c_customer_coupons")
        }

        assert "uq_d2c_customer_coupons_code" in unique_names
        assert "ck_d2c_customer_coupons_used_after_claimed" in check_names
        assert "ix_d2c_customer_coupons_customer_id" in index_names
        assert "ix_d2c_customer_coupons_status" in index_names
        assert "ix_d2c_customer_coupons_publish_version" in index_names
        assert "ix_d2c_customer_coupons_coupon_code" in index_names
        assert "ix_d2c_customer_coupons_promotion_code" in index_names
        assert "ix_d2c_customer_coupons_order_no" in index_names
        assert "ix_d2c_customer_coupons_coupon_id" not in index_names
    finally:
        engine.dispose()


def test_customer_coupon_usage_fact_foreign_keys_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_customer_coupons")
        }

        assert fk_targets == {"d2c_customers", "d2c_orders"}
    finally:
        engine.dispose()
