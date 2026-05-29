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
