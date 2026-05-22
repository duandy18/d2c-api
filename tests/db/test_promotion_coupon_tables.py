from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_promotion_coupon_tables_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert "d2c_promotions" in table_names
        assert "d2c_promotion_targets" in table_names
        assert "d2c_coupons" in table_names
        assert "d2c_customer_coupons" in table_names
    finally:
        engine.dispose()


def test_promotion_table_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns("d2c_promotions")}

        assert {
            "id",
            "promotion_code",
            "name",
            "description",
            "promotion_type",
            "discount_type",
            "discount_value",
            "scope_type",
            "min_order_amount_cents",
            "max_discount_cents",
            "currency",
            "starts_at",
            "ends_at",
            "status",
            "priority",
            "stackable",
            "is_active",
            "created_at",
            "updated_at",
        }.issubset(columns)
    finally:
        engine.dispose()


def test_coupon_table_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        coupon_columns = {column["name"] for column in inspector.get_columns("d2c_coupons")}
        customer_coupon_columns = {
            column["name"] for column in inspector.get_columns("d2c_customer_coupons")
        }

        assert {
            "id",
            "coupon_code",
            "name",
            "promotion_id",
            "coupon_type",
            "total_limit",
            "per_customer_limit",
            "starts_at",
            "ends_at",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        }.issubset(coupon_columns)

        assert {
            "id",
            "customer_coupon_code",
            "coupon_id",
            "customer_id",
            "status",
            "claimed_at",
            "used_at",
            "order_id",
            "created_at",
            "updated_at",
        }.issubset(customer_coupon_columns)
    finally:
        engine.dispose()


def test_promotion_coupon_constraints_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        promotion_unique_names = {
            constraint["name"] for constraint in inspector.get_unique_constraints("d2c_promotions")
        }
        target_unique_names = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_promotion_targets")
        }
        coupon_unique_names = {
            constraint["name"] for constraint in inspector.get_unique_constraints("d2c_coupons")
        }
        customer_coupon_unique_names = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_customer_coupons")
        }

        assert "uq_d2c_promotions_code" in promotion_unique_names
        assert "uq_d2c_promotion_targets_scope" in target_unique_names
        assert "uq_d2c_coupons_code" in coupon_unique_names
        assert "uq_d2c_customer_coupons_code" in customer_coupon_unique_names

        promotion_check_names = {
            constraint["name"] for constraint in inspector.get_check_constraints("d2c_promotions")
        }
        coupon_check_names = {
            constraint["name"] for constraint in inspector.get_check_constraints("d2c_coupons")
        }
        customer_coupon_check_names = {
            constraint["name"]
            for constraint in inspector.get_check_constraints("d2c_customer_coupons")
        }

        assert "ck_d2c_promotions_discount_value_positive" in promotion_check_names
        assert "ck_d2c_promotions_percentage_value_valid" in promotion_check_names
        assert "ck_d2c_coupons_total_limit_positive" in coupon_check_names
        assert "ck_d2c_customer_coupons_used_after_claimed" in customer_coupon_check_names
    finally:
        engine.dispose()


def test_promotion_coupon_foreign_keys_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        target_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_promotion_targets")
        }
        coupon_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_coupons")
        }
        customer_coupon_fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_customer_coupons")
        }

        assert target_fk_targets == {"d2c_promotions"}
        assert coupon_fk_targets == {"d2c_promotions"}
        assert {"d2c_coupons", "d2c_customers", "d2c_orders"}.issubset(customer_coupon_fk_targets)
    finally:
        engine.dispose()
