"""Fixed storefront Slot registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlotSpec:
    slot_code: str
    slot_type: str
    slot_group: str
    supports_items: bool
    supports_offers: bool


HOME_SLOT_SPECS: dict[str, SlotSpec] = {
    "header.brand": SlotSpec("header.brand", "brand", "header", False, False),
    "header.login_link": SlotSpec("header.login_link", "login_link", "header", False, False),
    "product_collection.tabs": SlotSpec(
        "product_collection.tabs", "collection_tabs", "navigation", True, False
    ),
    "hero.title": SlotSpec("hero.title", "hero", "main", False, False),
    "campaign.banner": SlotSpec("campaign.banner", "campaign_banner", "main", False, False),
    "product_category.nav": SlotSpec(
        "product_category.nav", "category_nav", "navigation", True, False
    ),
    "cart.entry": SlotSpec("cart.entry", "cart_entry", "navigation", False, False),
    "product_grid.list": SlotSpec("product_grid.list", "product_grid", "commerce", False, True),
    "service.promise_bar": SlotSpec(
        "service.promise_bar", "service_promise_bar", "footer", True, False
    ),
    "site.legal_footer": SlotSpec("site.legal_footer", "legal_footer", "footer", True, False),
}


def get_home_slot_spec(slot_code: str) -> SlotSpec | None:
    return HOME_SLOT_SPECS.get(slot_code)


def require_home_slot_spec(slot_code: str) -> SlotSpec:
    spec = get_home_slot_spec(slot_code)
    if spec is None:
        raise KeyError(slot_code)
    return spec
