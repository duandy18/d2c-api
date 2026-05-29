"""Clean local E2E/demo transaction residue from the D2C dev database."""
from __future__ import annotations

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

E2E_EMAIL_PATTERNS = [
    "%e2e%@example.test",
    "%bo-form%@example.test",
    "%register-debug%@example.test",
    "%phone-conflict%@example.test",
]

E2E_CART_PATTERNS = [
    "%e2e%",
    "%bo-form%",
    "%phone-fix%",
    "%final%",
    "%engine%",
]


def _database_url() -> str:
    return os.getenv(
        "D2C_DATABASE_URL",
        "postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c",
    )


def _pattern_clause(column_name: str, patterns: list[str]) -> tuple[str, dict[str, str]]:
    clauses: list[str] = []
    params: dict[str, str] = {}

    for index, pattern in enumerate(patterns):
        key = f"pattern_{index}"
        clauses.append(f"{column_name} LIKE :{key}")
        params[key] = pattern

    return " OR ".join(clauses), params


def _fetch_ids(connection: Connection, sql: str, params: dict[str, object]) -> list[int]:
    return [int(row[0]) for row in connection.execute(text(sql), params).all()]


def _delete_in_chunks(
    connection: Connection,
    table_name: str,
    column_name: str,
    ids: list[int],
) -> int:
    if not ids:
        return 0

    result = connection.execute(
        text(f"DELETE FROM {table_name} WHERE {column_name} = ANY(:ids)"),
        {"ids": ids},
    )
    return int(result.rowcount or 0)


def main() -> None:
    engine = create_engine(_database_url())
    summary: dict[str, int] = {}

    try:
        with engine.begin() as connection:
            email_clause, email_params = _pattern_clause("email", E2E_EMAIL_PATTERNS)
            customer_ids = _fetch_ids(
                connection,
                f"SELECT id FROM d2c_customers WHERE {email_clause}",
                email_params,
            )

            cart_clause, cart_params = _pattern_clause("anonymous_id", E2E_CART_PATTERNS)
            cart_ids = _fetch_ids(
                connection,
                f"""
                SELECT id
                FROM d2c_carts
                WHERE ({cart_clause})
                   OR customer_id = ANY(:customer_ids)
                """,
                {**cart_params, "customer_ids": customer_ids},
            )

            order_ids = _fetch_ids(
                connection,
                """
                SELECT id
                FROM d2c_orders
                WHERE customer_id = ANY(:customer_ids)
                   OR cart_id = ANY(:cart_ids)
                """,
                {"customer_ids": customer_ids, "cart_ids": cart_ids},
            )

            summary["payments"] = _delete_in_chunks(
                connection,
                "d2c_payments",
                "order_id",
                order_ids,
            )
            summary["customer_coupons"] = _delete_in_chunks(
                connection,
                "d2c_customer_coupons",
                "order_id",
                order_ids,
            )
            summary["order_lines"] = _delete_in_chunks(
                connection,
                "d2c_order_lines",
                "order_id",
                order_ids,
            )
            summary["orders"] = _delete_in_chunks(connection, "d2c_orders", "id", order_ids)
            summary["cart_lines"] = _delete_in_chunks(
                connection,
                "d2c_cart_lines",
                "cart_id",
                cart_ids,
            )
            summary["carts"] = _delete_in_chunks(connection, "d2c_carts", "id", cart_ids)
            summary["customer_sessions"] = _delete_in_chunks(
                connection,
                "d2c_customer_sessions",
                "customer_id",
                customer_ids,
            )
            summary["customer_password_credentials"] = _delete_in_chunks(
                connection,
                "d2c_customer_password_credentials",
                "customer_id",
                customer_ids,
            )
            summary["customer_addresses"] = _delete_in_chunks(
                connection,
                "d2c_customer_addresses",
                "customer_id",
                customer_ids,
            )
            summary["behavior_events"] = _delete_in_chunks(
                connection,
                "d2c_behavior_events",
                "customer_id",
                customer_ids,
            )
            summary["visitor_sessions"] = _delete_in_chunks(
                connection,
                "d2c_visitor_sessions",
                "customer_id",
                customer_ids,
            )
            summary["customers"] = _delete_in_chunks(
                connection,
                "d2c_customers",
                "id",
                customer_ids,
            )
    finally:
        engine.dispose()

    print({"ok": True, "deleted": summary})


if __name__ == "__main__":
    main()
