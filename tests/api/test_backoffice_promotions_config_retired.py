from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def test_backoffice_promotions_config_routes_are_retired() -> None:
    client = TestClient(app)

    get_paths = (
        "/backoffice/promotions/health",
        "/backoffice/promotions",
        "/backoffice/promotions/targets",
        "/backoffice/promotions/coupons",
    )
    post_paths = (
        "/backoffice/promotions",
        "/backoffice/promotions/UNKNOWN-PROMO/activate",
        "/backoffice/promotions/UNKNOWN-PROMO/deactivate",
        "/backoffice/promotions/UNKNOWN-PROMO/coupons",
        "/backoffice/promotions/coupons/UNKNOWN-COUPON/activate",
        "/backoffice/promotions/coupons/UNKNOWN-COUPON/deactivate",
    )

    for path in get_paths:
        response = client.get(path, headers=BACKOFFICE_HEADERS)
        assert response.status_code == 404

    for path in post_paths:
        response = client.post(path, headers=BACKOFFICE_HEADERS)
        assert response.status_code == 404


def test_backoffice_customer_coupons_requires_backoffice_client() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/promotions/customer-coupons")

    assert response.status_code == 401
    assert response.json() == {"detail": "backoffice_client_required"}


def test_backoffice_customer_coupons_usage_facts_remain_available() -> None:
    client = TestClient(app)

    response = client.get(
        "/backoffice/promotions/customer-coupons",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 200
    assert "count" in response.json()
    assert "customer_coupons" in response.json()
