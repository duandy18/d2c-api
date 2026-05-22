from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def test_backoffice_pages_health_requires_backoffice_client() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/pages/health")

    assert response.status_code == 401
    assert response.json() == {"detail": "backoffice_client_required"}


def test_backoffice_pages_health() -> None:
    client = TestClient(app)

    response = client.get(
        "/backoffice/pages/health",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "backoffice_pages",
        "surface": "merchant_navigation",
    }


def test_backoffice_pages_registry_contains_full_blueprint() -> None:
    client = TestClient(app)

    response = client.get(
        "/backoffice/pages/registry",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()
    page_by_code = {page["page_code"]: page for page in payload["pages"]}

    assert payload["count"] >= 50

    assert page_by_code["d2c.backoffice.operations"]["title"] == "经营首页"
    assert (
        page_by_code["d2c.backoffice.catalog_pricing.catalog.products"]["implementation_status"]
        == "ready"
    )
    assert (
        page_by_code["d2c.backoffice.marketing.coupons.customer_usage"]["data_status"]
        == "connected"
    )
    assert (
        page_by_code["d2c.backoffice.orders_fulfillment.orders.list"]["implementation_status"]
        == "planned"
    )
    assert (
        page_by_code["d2c.backoffice.analytics.funnel.checkout_to_paid"]["data_status"]
        == "placeholder"
    )
    assert page_by_code["d2c.backoffice.system.pages.registry"]["component_key"] == (
        "system.pages.registry"
    )


def test_backoffice_pages_navigation_returns_tree() -> None:
    client = TestClient(app)

    response = client.get(
        "/backoffice/pages/navigation",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["surface"] == "backoffice"
    assert payload["version"] == 1

    root_titles = [page["title"] for page in payload["pages"]]
    assert root_titles[:4] == ["经营首页", "商品与价格", "订单与履约", "营销中心"]

    catalog_root = next(page for page in payload["pages"] if page["title"] == "商品与价格")
    catalog_groups = {page["title"]: page for page in catalog_root["children"]}

    assert {"商品管理", "价格管理"}.issubset(catalog_groups)

    product_pages = {page["title"]: page for page in catalog_groups["商品管理"]["children"]}

    assert product_pages["商品列表"]["component_key"] == "catalog.products"
    assert product_pages["类目管理"]["implementation_status"] == "planned"

    marketing_root = next(page for page in payload["pages"] if page["title"] == "营销中心")
    marketing_groups = {page["title"]: page for page in marketing_root["children"]}

    assert {"促销管理", "优惠券管理"}.issubset(marketing_groups)
