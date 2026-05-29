from pathlib import Path


def test_storefront_pages_surface_migration_adds_route_fields() -> None:
    text = Path("alembic/versions/0033_sf_pages.py").read_text(encoding="utf-8")

    for token in (
        "auth_required",
        "navigation_label",
        "navigation_group",
        "sort_order",
        "ck_d2c_sf_pages_route_abs",
        "ix_d2c_sf_pages_route",
        "ix_d2c_sf_pages_nav",
    ):
        assert token in text


def test_storefront_pages_surface_migration_seeds_independent_pages() -> None:
    text = Path("alembic/versions/0033_sf_pages.py").read_text(encoding="utf-8")

    for token in (
        "home",
        "cart",
        "login",
        "register",
        "checkout",
        "/cart",
        "/login",
        "/register",
        "/checkout",
    ):
        assert token in text



def test_storefront_payment_result_page_migration_seeds_result_page() -> None:
    text = Path("alembic/versions/0034_pay_result.py").read_text(encoding="utf-8")

    for token in (
        "payment_result",
        "/payment-result",
        "支付结果",
        "auth_required",
        "sort_order",
    ):
        assert token in text



def test_storefront_account_security_page_migration_seeds_security_page() -> None:
    text = Path("alembic/versions/0035_acct_sec.py").read_text(encoding="utf-8")

    for token in (
        "account_security",
        "/account/security",
        "账户安全",
        "auth_required",
        "sort_order",
    ):
        assert token in text



def test_storefront_my_center_page_migration_replaces_account_security() -> None:
    text = Path("alembic/versions/0036_my_center.py").read_text(encoding="utf-8")

    for token in (
        "account_security",
        "my_home",
        "my_orders",
        "my_account",
        "my_security",
        "/my",
        "/my/orders",
        "/my/account",
        "/my/security",
        "我的购买记录",
        "我的账号",
    ):
        assert token in text
