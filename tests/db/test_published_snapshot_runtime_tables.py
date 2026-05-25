from __future__ import annotations

from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_engine


def test_terminal_published_snapshot_runtime_tables_exist() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        assert {
            "d2c_published_groups",
            "d2c_published_offers",
            "d2c_published_offer_components",
            "d2c_published_offer_prices",
            "d2c_published_offer_positions",
            "d2c_published_storefront_sections",
            "d2c_published_storefront_section_layouts",
            "d2c_published_promotion_rules",
            "d2c_published_promotion_targets",
        }.issubset(table_names)

        assert "d2c_published_coupons" in table_names
    finally:
        engine.dispose()


def test_terminal_published_snapshot_runtime_columns_exist() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)

        group_columns = {column["name"] for column in inspector.get_columns("d2c_published_groups")}
        offer_columns = {column["name"] for column in inspector.get_columns("d2c_published_offers")}
        component_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_offer_components")
        }
        price_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_offer_prices")
        }
        position_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_offer_positions")
        }
        section_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_storefront_sections")
        }
        layout_columns = {
            column["name"]
            for column in inspector.get_columns("d2c_published_storefront_section_layouts")
        }
        rule_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_promotion_rules")
        }
        target_columns = {
            column["name"] for column in inspector.get_columns("d2c_published_promotion_targets")
        }

        assert {"publish_version", "group_code", "group_name", "group_kind"}.issubset(group_columns)
        assert {"publish_version", "offer_code", "offer_type", "title"}.issubset(offer_columns)
        assert {
            "publish_version",
            "offer_code",
            "component_no",
            "pms_item_id",
            "sku_code",
            "quantity",
        }.issubset(component_columns)
        assert {"publish_version", "offer_code", "price_code", "price_cents"}.issubset(
            price_columns
        )
        assert {"publish_version", "position_code", "group_code", "offer_code"}.issubset(
            position_columns
        )
        assert {"publish_version", "section_code", "section_type", "group_code", "title"}.issubset(
            section_columns
        )
        assert {
            "publish_version",
            "section_code",
            "display_type",
            "columns_desktop",
            "columns_tablet",
            "columns_mobile",
            "card_size",
            "image_ratio",
        }.issubset(layout_columns)
        assert {
            "publish_version",
            "promotion_code",
            "promotion_name",
            "threshold_amount_cents",
            "display_badge",
        }.issubset(rule_columns)
        assert {"publish_version", "promotion_code", "target_type"}.issubset(target_columns)
    finally:
        engine.dispose()


def test_terminal_coupon_runtime_no_longer_depends_on_legacy_promotion_table() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        inspector = inspect(engine)
        fk_targets = {
            fk["referred_table"] for fk in inspector.get_foreign_keys("d2c_published_coupons")
        }
        index_names = {index["name"] for index in inspector.get_indexes("d2c_published_coupons")}

        assert "d2c_published_promotions" not in fk_targets
        assert "ix_d2c_pub_coupons_rule" in index_names
    finally:
        engine.dispose()
