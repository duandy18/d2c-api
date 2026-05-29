from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.published_catalog import seed_default_published_catalog

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}
OFFER_CODE = "offer-cat-food-salmon-001"


def _put_home_position(client: TestClient) -> None:
    response = client.put(
        "/backoffice/site-config/pages/home/slots/product_grid.list/offer-positions",
        headers=BACKOFFICE_HEADERS,
        json={
            "offer_positions": [
                {
                    "position_code": "test-home-pos-display-metrics",
                    "offer_code": OFFER_CODE,
                    "position_type": "manual",
                    "is_featured": True,
                    "sort_order": 10,
                    "is_active": True,
                    "visible_from": None,
                    "visible_until": None,
                }
            ]
        },
    )

    assert response.status_code == 200


def _home_offer(client: TestClient) -> dict[str, object]:
    home_response = client.get("/storefront/home")
    assert home_response.status_code == 200

    product_slot = next(
        slot
        for slot in home_response.json()["page"]["slots"]
        if slot["slot_code"] == "product_grid.list"
    )

    return next(
        position["offer"]
        for position in product_slot["offers"]
        if position["offer_code"] == OFFER_CODE
    )


def test_backoffice_offer_display_metrics_roundtrip_and_storefront_home() -> None:
    seed_default_published_catalog()
    client = TestClient(app)
    _put_home_position(client)

    patch_response = client.patch(
        f"/backoffice/site-config/offers/{OFFER_CODE}/display-metrics",
        headers=BACKOFFICE_HEADERS,
        json={
            "display_sold_quantity": 238,
            "display_paid_customer_count": 86,
            "display_stock_quantity": 12,
            "is_active": True,
        },
    )

    assert patch_response.status_code == 200
    assert patch_response.json() == {
        "offer_code": OFFER_CODE,
        "display_sold_quantity": 238,
        "display_paid_customer_count": 86,
        "display_stock_quantity": 12,
        "is_active": True,
    }

    get_response = client.get(
        f"/backoffice/site-config/offers/{OFFER_CODE}/display-metrics",
        headers=BACKOFFICE_HEADERS,
    )

    assert get_response.status_code == 200
    assert get_response.json()["display_sold_quantity"] == 238
    assert get_response.json()["display_paid_customer_count"] == 86
    assert get_response.json()["display_stock_quantity"] == 12

    offer = _home_offer(client)

    assert offer["sold_quantity"] == 238
    assert offer["paid_customer_count"] == 86
    assert offer["display_stock_quantity"] == 12
    assert offer["stock_status"] == "in_stock"
