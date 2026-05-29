from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.published_catalog import seed_default_published_catalog

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}
OFFER_CODE = "offer-cat-food-salmon-001"


def _cart_identity(prefix: str) -> dict[str, str]:
    suffix = uuid4().hex[:10]
    return {
        "anonymous_id": f"display-stock-{prefix}-anon-{suffix}",
        "session_code": f"display-stock-{prefix}-session-{suffix}",
    }


def _put_home_position(client: TestClient) -> None:
    response = client.put(
        "/backoffice/site-config/pages/home/slots/product_grid.list/offer-positions",
        headers=BACKOFFICE_HEADERS,
        json={
            "offer_positions": [
                {
                    "position_code": "test-home-pos-display-stock-gate",
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


def _set_display_stock(client: TestClient, stock_quantity: int) -> None:
    response = client.patch(
        f"/backoffice/site-config/offers/{OFFER_CODE}/display-metrics",
        headers=BACKOFFICE_HEADERS,
        json={
            "display_sold_quantity": 238,
            "display_paid_customer_count": 86,
            "display_stock_quantity": stock_quantity,
            "is_active": True,
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


def test_display_stock_zero_keeps_offer_visible_but_blocks_cart_add() -> None:
    seed_default_published_catalog()
    client = TestClient(app)
    _put_home_position(client)
    _set_display_stock(client, 0)
    identity = _cart_identity("zero")

    offer = _home_offer(client)

    assert offer["display_stock_quantity"] == 0
    assert offer["stock_status"] == "out_of_stock"
    assert offer["sell_status"] == "sellable"

    add_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": OFFER_CODE,
            "quantity": 1,
        },
    )

    assert add_response.status_code == 409
    assert add_response.json() == {"detail": "cart_offer_display_stock_unavailable"}


def test_display_stock_caps_cart_quantity() -> None:
    seed_default_published_catalog()
    client = TestClient(app)
    _set_display_stock(client, 1)
    identity = _cart_identity("cap")

    too_many_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": OFFER_CODE,
            "quantity": 2,
        },
    )

    assert too_many_response.status_code == 409
    assert too_many_response.json() == {"detail": "cart_offer_quantity_exceeds_display_stock"}

    ok_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": OFFER_CODE,
            "quantity": 1,
        },
    )

    assert ok_response.status_code == 200
    assert ok_response.json()["item_count"] == 1
