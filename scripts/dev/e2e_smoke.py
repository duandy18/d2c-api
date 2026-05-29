"""Run local D2C API end-to-end smoke through site config, cart, checkout, pay."""
from __future__ import annotations

import os
import time
from typing import Any

import httpx

BASE_URL = os.getenv("D2C_API_BASE_URL", "http://127.0.0.1:8025").rstrip("/")
BACKOFFICE_HEADERS = {"X-Backoffice-Client": os.getenv("D2C_BACKOFFICE_CLIENT", "d2c-backoffice")}


def _show(title: str, value: Any) -> None:
    print(f"\n===== {title} =====")
    print(value)


def _request_json(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    json: Any | None = None,
    expected_status: int | tuple[int, ...] = 200,
) -> Any:
    response = client.request(method, f"{BASE_URL}{path}", headers=headers, json=json)
    expected = expected_status if isinstance(expected_status, tuple) else (expected_status,)
    print(f"{method} {path} -> {response.status_code}")

    if response.status_code not in expected:
        print(response.text)
        raise AssertionError(f"unexpected status: {method} {path} {response.status_code}")

    return response.json()


def main() -> None:
    timestamp = int(time.time())
    anonymous_id = f"make-e2e-anon-{timestamp}"
    session_code = f"make-e2e-session-{timestamp}"
    customer_email = f"make-e2e-{timestamp}@example.test"
    customer_phone = f"174{str(timestamp)[-8:]}"
    customer_password = "E2ePass1234!"

    hero_title = f"Make E2E 首页 {timestamp}"
    campaign_title = f"Make E2E 活动 {timestamp}"

    with httpx.Client(timeout=30.0) as client:
        health = _request_json(client, "GET", "/health")
        _show("health", health)

        catalog = _request_json(client, "GET", "/catalog/products")
        products = catalog.get("products", [])
        if not products:
            raise AssertionError("catalog has no products; run make seed-demo first")

        offer_code = str(products[0]["product_id"])
        _show("selected_offer_code", offer_code)

        resolved = _request_json(
            client,
            "GET",
            f"/backoffice/site-config/offers/{offer_code}/resolve",
            headers=BACKOFFICE_HEADERS,
        )
        _show("resolved_offer", resolved["offer"])

        _request_json(
            client,
            "PATCH",
            "/backoffice/site-config/pages/home",
            headers=BACKOFFICE_HEADERS,
            json={
                "title": "Make E2E 首页配置",
                "description": "make e2e-smoke 写入",
                "status": "active",
                "seo_title": "Make E2E 首页配置",
                "seo_description": "make e2e-smoke 写入",
            },
        )

        _request_json(
            client,
            "PATCH",
            "/backoffice/site-config/pages/home/slots/hero.title",
            headers=BACKOFFICE_HEADERS,
            json={
                "content": {
                    "kicker": "MAKE E2E",
                    "title": hero_title,
                },
                "presentation": {},
                "is_active": True,
            },
        )

        _request_json(
            client,
            "PATCH",
            "/backoffice/site-config/pages/home/slots/campaign.banner",
            headers=BACKOFFICE_HEADERS,
            json={
                "content": {
                    "label": "Smoke",
                    "title": campaign_title,
                    "subtitle": "由 make e2e-smoke 写入",
                    "link_target": "#products",
                },
                "presentation": {},
                "is_active": True,
            },
        )

        _request_json(
            client,
            "PUT",
            "/backoffice/site-config/pages/home/slots/product_grid.list/offer-positions",
            headers=BACKOFFICE_HEADERS,
            json={
                "offer_positions": [
                    {
                        "position_code": f"make-e2e-home-{timestamp}",
                        "offer_code": offer_code,
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

        home = _request_json(client, "GET", "/storefront/home")
        home_slots = {slot["slot_code"]: slot for slot in home["page"]["slots"]}
        assert home_slots["hero.title"]["content"]["title"] == hero_title
        assert home_slots["campaign.banner"]["content"]["title"] == campaign_title
        assert any(
            position["offer_code"] == offer_code
            for position in home_slots["product_grid.list"]["offers"]
        )
        _show(
            "storefront_home_verified",
            {"offer_count": len(home_slots["product_grid.list"]["offers"])},
        )

        cart = _request_json(
            client,
            "POST",
            "/cart/items",
            json={
                "anonymous_id": anonymous_id,
                "session_code": session_code,
                "offer_code": offer_code,
                "quantity": 1,
            },
        )
        _show("cart", {"cart_code": cart["cart_code"], "item_count": cart["item_count"]})

        auth = _request_json(
            client,
            "POST",
            "/customers/register",
            json={
                "email": customer_email,
                "password": customer_password,
                "display_name": "Make E2E Customer",
                "phone": customer_phone,
            },
            expected_status=(200, 201),
        )
        token = str(auth["access_token"])

        order = _request_json(
            client,
            "POST",
            "/orders/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cart_code": cart["cart_code"],
                "recipient_name": "Make E2E Customer",
                "recipient_phone": customer_phone,
                "shipping_country": "US",
                "shipping_province": "CA",
                "shipping_city": "Los Angeles",
                "shipping_district": None,
                "shipping_address_line1": "1 Make E2E Street",
                "shipping_address_line2": None,
                "shipping_postal_code": "90001",
                "payment_provider": "mock",
                "payment_method": "mock",
                "coupon_code": None,
            },
            expected_status=(200, 201),
        )

        paid = _request_json(
            client,
            "POST",
            f"/orders/{order['order_no']}/pay/mock",
            headers={"Authorization": f"Bearer {token}"},
        )

        result = {
            "ok": True,
            "base_url": BASE_URL,
            "offer_code": offer_code,
            "cart_code": cart["cart_code"],
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "order_no": paid["order_no"],
            "order_status": paid["status"],
            "hero_title": hero_title,
            "campaign_title": campaign_title,
        }
        _show("E2E_SMOKE_RESULT", result)


if __name__ == "__main__":
    main()
