"""Slot-first site configuration boundary tests."""

from pathlib import Path


def test_storefront_home_route_uses_slot_first_site_config_service() -> None:
    route_text = Path("app/api/routes/storefront/home.py").read_text(encoding="utf-8")

    assert "app.domains.site_config.contracts.storefront_home_contract" in route_text
    assert "app.domains.site_config.services.storefront_home_service" in route_text
    assert "app.domains.storefront.services.home_service" not in route_text


def test_site_config_domain_does_not_import_site_builder() -> None:
    for path in Path("app/domains/site_config").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "site_builder" not in text
        assert "d2c-site-builder" not in text


def test_storefront_home_contract_is_slot_first() -> None:
    text = Path(
        "app/domains/site_config/contracts/storefront_home_contract.py"
    ).read_text(encoding="utf-8")

    assert 'Literal["d2c_storefront_site_config"]' in text
    assert "class StorefrontHomeSlot" in text
    assert "slots: list[StorefrontHomeSlot]" in text
    assert "StorefrontHomeRegion" not in text
    assert "StorefrontHomeBlock" not in text


def test_slot_offer_position_owner_does_not_store_product_facts() -> None:
    model_text = Path(
        "app/domains/site_config/models/storefront_site_config.py"
    ).read_text(encoding="utf-8")
    migration_text = Path("alembic/versions/0030_site_config_slots.py").read_text(
        encoding="utf-8"
    )

    combined = model_text + "\n" + migration_text
    owner_area = combined.split("StorefrontSlotOfferPosition", maxsplit=1)[-1]

    assert "sale_price" not in owner_area
    assert "price_cents" not in owner_area
    assert "stock_status" not in owner_area
    assert "inventory" not in owner_area
