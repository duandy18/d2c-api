from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_payment_table_exists_after_migration() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        assert "d2c_payments" in inspector.get_table_names()
    finally:
        engine.dispose()


def test_order_checkout_payment_columns_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        order_columns = {column["name"] for column in inspector.get_columns("d2c_orders")}
        payment_columns = {column["name"] for column in inspector.get_columns("d2c_payments")}

        assert {"cart_code", "paid_at"}.issubset(order_columns)
        assert {
            "id",
            "payment_no",
            "order_id",
            "order_no",
            "customer_id",
            "amount_cents",
            "currency",
            "provider",
            "payment_method",
            "status",
            "provider_payment_id",
            "provider_trade_no",
            "payment_reference",
            "notify_payload",
            "failure_reason",
            "paid_at",
            "created_at",
            "updated_at",
        }.issubset(payment_columns)
    finally:
        engine.dispose()


def test_payment_constraints_and_indexes_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        unique_constraints = inspector.get_unique_constraints("d2c_payments")
        unique_names = {constraint["name"] for constraint in unique_constraints}
        assert "uq_d2c_payments_payment_no" in unique_names

        check_constraints = inspector.get_check_constraints("d2c_payments")
        check_names = {constraint["name"] for constraint in check_constraints}
        assert "ck_d2c_payments_amount_cents_non_negative" in check_names

        foreign_key_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_payments")
        }
        assert {"d2c_orders", "d2c_customers"}.issubset(foreign_key_targets)
    finally:
        engine.dispose()
