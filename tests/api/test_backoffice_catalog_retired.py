from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def test_backoffice_catalog_routes_are_retired() -> None:
    client = TestClient(app)

    for path in (
        "/backoffice/catalog/health",
        "/backoffice/catalog/units",
        "/backoffice/catalog/price-lists",
        "/backoffice/catalog/products",
        "/backoffice/catalog/skus",
        "/backoffice/catalog/sku-prices",
    ):
        response = client.get(path, headers=BACKOFFICE_HEADERS)
        assert response.status_code == 404


def test_backoffice_customer_coupon_usage_route_remains_available() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/promotions/customer-coupons", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200
    assert "count" in response.json()
    assert "customer_coupons" in response.json()
