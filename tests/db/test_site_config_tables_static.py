"""Static table-contract tests for Slot-first site configuration."""

from pathlib import Path


def test_site_config_migration_creates_slot_first_owner_tables() -> None:
    text = Path("alembic/versions/0030_site_config_slots.py").read_text(encoding="utf-8")

    assert "d2c_storefront_sites" in text
    assert "d2c_storefront_theme_settings" in text
    assert "d2c_storefront_pages" in text
    assert "d2c_storefront_page_slots" in text
    assert "d2c_storefront_slot_items" in text
    assert "d2c_storefront_slot_offer_positions" in text
    assert "d2c_storefront_page_configs" not in text


def test_default_home_seed_contains_known_slots() -> None:
    text = Path("alembic/versions/0030_site_config_slots.py").read_text(encoding="utf-8")

    for slot_code in (
        "header.brand",
        "header.login_link",
        "product_collection.tabs",
        "hero.title",
        "campaign.banner",
        "product_category.nav",
        "cart.entry",
        "product_grid.list",
        "service.promise_bar",
        "site.legal_footer",
    ):
        assert slot_code in text
