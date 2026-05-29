from fastapi.testclient import TestClient

from app.main import app


def test_storefront_pages_returns_independent_page_surface() -> None:
    client = TestClient(app)

    response = client.get("/storefront/pages")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_storefront_pages"
    assert payload["count"] >= 7

    pages = {page["page_code"]: page for page in payload["pages"]}

    assert pages["home"]["route_path"] == "/"
    assert pages["home"]["auth_required"] is False
    assert pages["home"]["navigation_label"] == "首页"

    assert pages["cart"]["route_path"] == "/cart"
    assert pages["cart"]["auth_required"] is False

    assert pages["login"]["route_path"] == "/login"
    assert pages["login"]["auth_required"] is False

    assert pages["register"]["route_path"] == "/register"
    assert pages["register"]["auth_required"] is False

    assert pages["checkout"]["route_path"] == "/checkout"
    assert pages["checkout"]["auth_required"] is True

    assert pages["payment_result"]["route_path"] == "/payment-result"
    assert pages["payment_result"]["auth_required"] is True
    assert pages["payment_result"]["navigation_label"] == "支付结果"

    assert pages["account_security"]["route_path"] == "/account/security"
    assert pages["account_security"]["auth_required"] is True
    assert pages["account_security"]["navigation_label"] == "账户安全"

    sort_orders = [page["sort_order"] for page in payload["pages"]]
    assert sort_orders == sorted(sort_orders)


def test_storefront_pages_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/storefront/pages")

    assert response.status_code == 200


def test_storefront_pages_contract_does_not_embed_page_content() -> None:
    client = TestClient(app)

    response = client.get("/storefront/pages")

    assert response.status_code == 200

    page = response.json()["pages"][0]
    assert "slots" not in page
    assert "offers" not in page
    assert "items" not in page
