"""Seed deterministic D2C demo data for local development.

This script is intentionally scoped to the local/dev D2C database. It creates a
stable published runtime catalog and points the default home page product grid
at those demo offers. It does not create orders or customers.
"""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

DEMO_VERSION = "DEMO-PUB-LOCAL-001"
DEMO_GROUP_CODE = "demo_cat_essentials"
DEMO_PUBLISHED_AT = datetime.now(UTC)

DEMO_OFFERS = [
    {
        "offer_code": "demo-cat-food-salmon-1kg",
        "price_code": "demo-price-cat-food-salmon-1kg",
        "position_code": "demo-home-pos-cat-food-salmon-1kg",
        "title": "三文鱼成猫粮 1kg",
        "subtitle": "高蛋白日常主粮",
        "description": "适合成年猫日常喂养的三文鱼配方猫粮。",
        "image_url": "https://example.test/demo/cat-food-salmon-1kg.png",
        "price_cents": 1899,
        "compare_at_price_cents": 2299,
        "sku_code": "CAT-FOOD-SALMON-1KG",
        "pms_sku": "PMS-CAT-FOOD-SALMON",
        "barcode": "6900000000000",
        "sort_order": 10,
        "source_offer_id": 501,
        "source_price_id": 701,
        "source_position_id": 801,
        "pms_item_id": 1001,
        "pms_sku_code_id": 2001,
        "pms_item_uom_id": 3001,
    },
    {
        "offer_code": "demo-cat-litter-tofu-6l",
        "price_code": "demo-price-cat-litter-tofu-6l",
        "position_code": "demo-home-pos-cat-litter-tofu-6l",
        "title": "豆腐猫砂 6L",
        "subtitle": "低尘结团易清理",
        "description": "低尘豆腐猫砂，适合日常家庭使用。",
        "image_url": "https://example.test/demo/cat-litter-tofu-6l.png",
        "price_cents": 1099,
        "compare_at_price_cents": 1399,
        "sku_code": "CAT-LITTER-TOFU-6L",
        "pms_sku": "PMS-CAT-LITTER-TOFU",
        "barcode": "6900000000001",
        "sort_order": 20,
        "source_offer_id": 502,
        "source_price_id": 702,
        "source_position_id": 802,
        "pms_item_id": 1002,
        "pms_sku_code_id": 2002,
        "pms_item_uom_id": 3002,
    },
]


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _database_url() -> str:
    return os.getenv(
        "D2C_DATABASE_URL",
        "postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c",
    )


def _slot_id(connection: Connection, slot_code: str) -> int:
    slot_id = connection.execute(
        text(
            """
            SELECT ps.id
            FROM d2c_storefront_page_slots ps
            JOIN d2c_storefront_pages p ON p.id = ps.page_id
            JOIN d2c_storefront_sites s ON s.id = p.site_id
            WHERE s.site_code = 'default'
              AND p.page_code = 'home'
              AND ps.slot_code = :slot_code
            """
        ),
        {"slot_code": slot_code},
    ).scalar_one_or_none()

    if slot_id is None:
        raise RuntimeError(f"default home slot not found: {slot_code}")

    return int(slot_id)


def _seed_published_catalog(connection: Connection) -> None:
    connection.execute(
        text(
            """
            INSERT INTO d2c_published_groups (
              publish_version,
              group_code,
              group_name,
              group_kind,
              description,
              image_url,
              sort_order,
              display_status,
              is_active,
              source_group_id,
              raw_payload,
              published_at
            )
            VALUES (
              :publish_version,
              :group_code,
              :group_name,
              :group_kind,
              :description,
              :image_url,
              :sort_order,
              :display_status,
              :is_active,
              :source_group_id,
              CAST(:raw_payload AS json),
              :published_at
            )
            ON CONFLICT (publish_version, group_code) DO UPDATE SET
              group_name = EXCLUDED.group_name,
              group_kind = EXCLUDED.group_kind,
              description = EXCLUDED.description,
              image_url = EXCLUDED.image_url,
              sort_order = EXCLUDED.sort_order,
              display_status = EXCLUDED.display_status,
              is_active = EXCLUDED.is_active,
              source_group_id = EXCLUDED.source_group_id,
              raw_payload = EXCLUDED.raw_payload,
              published_at = EXCLUDED.published_at
            """
        ),
        {
            "publish_version": DEMO_VERSION,
            "group_code": DEMO_GROUP_CODE,
            "group_name": "猫用品精选",
            "group_kind": "category",
            "description": "本地演示用猫用品精选分类。",
            "image_url": None,
            "sort_order": 10,
            "display_status": "visible",
            "is_active": True,
            "source_group_id": 401,
            "raw_payload": _json({"source": "demo_seed"}),
            "published_at": DEMO_PUBLISHED_AT,
        },
    )

    for index, offer in enumerate(DEMO_OFFERS, start=1):
        connection.execute(
            text(
                """
                INSERT INTO d2c_published_offers (
                  publish_version,
                  offer_code,
                  offer_type,
                  title,
                  subtitle,
                  description,
                  image_url,
                  display_status,
                  sell_status,
                  source_offer_id,
                  raw_payload,
                  published_at
                )
                VALUES (
                  :publish_version,
                  :offer_code,
                  'single',
                  :title,
                  :subtitle,
                  :description,
                  :image_url,
                  'visible',
                  'sellable',
                  :source_offer_id,
                  CAST(:raw_payload AS json),
                  :published_at
                )
                ON CONFLICT (publish_version, offer_code) DO UPDATE SET
                  offer_type = EXCLUDED.offer_type,
                  title = EXCLUDED.title,
                  subtitle = EXCLUDED.subtitle,
                  description = EXCLUDED.description,
                  image_url = EXCLUDED.image_url,
                  display_status = EXCLUDED.display_status,
                  sell_status = EXCLUDED.sell_status,
                  source_offer_id = EXCLUDED.source_offer_id,
                  raw_payload = EXCLUDED.raw_payload,
                  published_at = EXCLUDED.published_at
                """
            ),
            {
                "publish_version": DEMO_VERSION,
                "offer_code": offer["offer_code"],
                "title": offer["title"],
                "subtitle": offer["subtitle"],
                "description": offer["description"],
                "image_url": offer["image_url"],
                "source_offer_id": offer["source_offer_id"],
                "raw_payload": _json({"source": "demo_seed", "demo_offer_index": index}),
                "published_at": DEMO_PUBLISHED_AT,
            },
        )

        connection.execute(
            text(
                """
                INSERT INTO d2c_published_offer_prices (
                  publish_version,
                  offer_code,
                  price_code,
                  channel,
                  currency,
                  price_cents,
                  compare_at_price_cents,
                  effective_from,
                  effective_until,
                  is_active,
                  priority,
                  source_price_id,
                  raw_payload,
                  published_at
                )
                VALUES (
                  :publish_version,
                  :offer_code,
                  :price_code,
                  'storefront',
                  'USD',
                  :price_cents,
                  :compare_at_price_cents,
                  NULL,
                  NULL,
                  TRUE,
                  10,
                  :source_price_id,
                  CAST(:raw_payload AS json),
                  :published_at
                )
                ON CONFLICT (publish_version, price_code) DO UPDATE SET
                  offer_code = EXCLUDED.offer_code,
                  channel = EXCLUDED.channel,
                  currency = EXCLUDED.currency,
                  price_cents = EXCLUDED.price_cents,
                  compare_at_price_cents = EXCLUDED.compare_at_price_cents,
                  effective_from = EXCLUDED.effective_from,
                  effective_until = EXCLUDED.effective_until,
                  is_active = EXCLUDED.is_active,
                  priority = EXCLUDED.priority,
                  source_price_id = EXCLUDED.source_price_id,
                  raw_payload = EXCLUDED.raw_payload,
                  published_at = EXCLUDED.published_at
                """
            ),
            {
                "publish_version": DEMO_VERSION,
                "offer_code": offer["offer_code"],
                "price_code": offer["price_code"],
                "price_cents": offer["price_cents"],
                "compare_at_price_cents": offer["compare_at_price_cents"],
                "source_price_id": offer["source_price_id"],
                "raw_payload": _json({"source": "demo_seed"}),
                "published_at": DEMO_PUBLISHED_AT,
            },
        )

        connection.execute(
            text(
                """
                INSERT INTO d2c_published_offer_components (
                  publish_version,
                  offer_code,
                  component_no,
                  pms_item_id,
                  pms_sku,
                  pms_sku_code_id,
                  sku_code,
                  pms_item_uom_id,
                  uom_code,
                  uom_name,
                  pms_barcode_id,
                  barcode,
                  quantity,
                  component_role,
                  sort_order,
                  required,
                  source_component_id,
                  raw_payload,
                  published_at
                )
                VALUES (
                  :publish_version,
                  :offer_code,
                  1,
                  :pms_item_id,
                  :pms_sku,
                  :pms_sku_code_id,
                  :sku_code,
                  :pms_item_uom_id,
                  'bag',
                  '袋',
                  NULL,
                  :barcode,
                  1,
                  'primary',
                  10,
                  TRUE,
                  :source_component_id,
                  CAST(:raw_payload AS json),
                  :published_at
                )
                ON CONFLICT (publish_version, offer_code, component_no) DO UPDATE SET
                  pms_item_id = EXCLUDED.pms_item_id,
                  pms_sku = EXCLUDED.pms_sku,
                  pms_sku_code_id = EXCLUDED.pms_sku_code_id,
                  sku_code = EXCLUDED.sku_code,
                  pms_item_uom_id = EXCLUDED.pms_item_uom_id,
                  uom_code = EXCLUDED.uom_code,
                  uom_name = EXCLUDED.uom_name,
                  pms_barcode_id = EXCLUDED.pms_barcode_id,
                  barcode = EXCLUDED.barcode,
                  quantity = EXCLUDED.quantity,
                  component_role = EXCLUDED.component_role,
                  sort_order = EXCLUDED.sort_order,
                  required = EXCLUDED.required,
                  source_component_id = EXCLUDED.source_component_id,
                  raw_payload = EXCLUDED.raw_payload,
                  published_at = EXCLUDED.published_at
                """
            ),
            {
                "publish_version": DEMO_VERSION,
                "offer_code": offer["offer_code"],
                "pms_item_id": offer["pms_item_id"],
                "pms_sku": offer["pms_sku"],
                "pms_sku_code_id": offer["pms_sku_code_id"],
                "sku_code": offer["sku_code"],
                "pms_item_uom_id": offer["pms_item_uom_id"],
                "barcode": offer["barcode"],
                "source_component_id": 900 + index,
                "raw_payload": _json({"source": "demo_seed"}),
                "published_at": DEMO_PUBLISHED_AT,
            },
        )

        connection.execute(
            text(
                """
                INSERT INTO d2c_published_offer_positions (
                  publish_version,
                  position_code,
                  group_code,
                  offer_code,
                  sort_order,
                  position_source,
                  is_featured,
                  visible_from,
                  visible_until,
                  is_active,
                  source_position_id,
                  raw_payload,
                  published_at
                )
                VALUES (
                  :publish_version,
                  :position_code,
                  :group_code,
                  :offer_code,
                  :sort_order,
                  'manual',
                  :is_featured,
                  NULL,
                  NULL,
                  TRUE,
                  :source_position_id,
                  CAST(:raw_payload AS json),
                  :published_at
                )
                ON CONFLICT (publish_version, position_code) DO UPDATE SET
                  group_code = EXCLUDED.group_code,
                  offer_code = EXCLUDED.offer_code,
                  sort_order = EXCLUDED.sort_order,
                  position_source = EXCLUDED.position_source,
                  is_featured = EXCLUDED.is_featured,
                  visible_from = EXCLUDED.visible_from,
                  visible_until = EXCLUDED.visible_until,
                  is_active = EXCLUDED.is_active,
                  source_position_id = EXCLUDED.source_position_id,
                  raw_payload = EXCLUDED.raw_payload,
                  published_at = EXCLUDED.published_at
                """
            ),
            {
                "publish_version": DEMO_VERSION,
                "position_code": offer["position_code"],
                "group_code": DEMO_GROUP_CODE,
                "offer_code": offer["offer_code"],
                "sort_order": offer["sort_order"],
                "is_featured": index == 1,
                "source_position_id": offer["source_position_id"],
                "raw_payload": _json({"source": "demo_seed"}),
                "published_at": DEMO_PUBLISHED_AT,
            },
        )


def _seed_home_config(connection: Connection) -> None:
    hero_slot_id = _slot_id(connection, "hero.title")
    campaign_slot_id = _slot_id(connection, "campaign.banner")
    product_grid_slot_id = _slot_id(connection, "product_grid.list")
    service_slot_id = _slot_id(connection, "service.promise_bar")
    legal_slot_id = _slot_id(connection, "site.legal_footer")

    connection.execute(
        text(
            """
            UPDATE d2c_storefront_pages
            SET title = 'D2C 演示独立站',
                description = '本地演示首页',
                status = 'active',
                seo_title = 'D2C 演示独立站',
                seo_description = '本地开发演示首页'
            WHERE page_code = 'home'
            """
        )
    )

    connection.execute(
        text(
            """
            UPDATE d2c_storefront_page_slots
            SET content_json = CAST(:content_json AS json),
                presentation_json = CAST(:presentation_json AS json),
                is_active = TRUE
            WHERE id = :slot_id
            """
        ),
        {
            "slot_id": hero_slot_id,
            "content_json": _json(
                {
                    "kicker": "D2C DEMO",
                    "title": "猫用品精选商城",
                }
            ),
            "presentation_json": _json({}),
        },
    )

    connection.execute(
        text(
            """
            UPDATE d2c_storefront_page_slots
            SET content_json = CAST(:content_json AS json),
                presentation_json = CAST(:presentation_json AS json),
                is_active = TRUE
            WHERE id = :slot_id
            """
        ),
        {
            "slot_id": campaign_slot_id,
            "content_json": _json(
                {
                    "label": "限时活动",
                    "title": "满 99 享精选好物",
                    "subtitle": "演示站点活动横幅",
                    "link_target": "#products",
                }
            ),
            "presentation_json": _json({}),
        },
    )

    connection.execute(
        text(
            """
            UPDATE d2c_storefront_page_slots
            SET title = '演示热卖商品',
                content_json = CAST(:content_json AS json),
                presentation_json = CAST(:presentation_json AS json),
                is_active = TRUE
            WHERE id = :slot_id
            """
        ),
        {
            "slot_id": product_grid_slot_id,
            "content_json": _json({}),
            "presentation_json": _json(
                {
                    "columns_desktop": 4,
                    "columns_tablet": 2,
                    "columns_mobile": 1,
                    "max_items": 8,
                    "show_promotion_badge": True,
                    "show_sales_summary": True,
                    "show_review_summary": True,
                    "show_compare_price": True,
                    "show_quantity_stepper": True,
                }
            ),
        },
    )

    connection.execute(
        text("DELETE FROM d2c_storefront_slot_offer_positions WHERE slot_id = :slot_id"),
        {"slot_id": product_grid_slot_id},
    )

    for offer in DEMO_OFFERS:
        connection.execute(
            text(
                """
                INSERT INTO d2c_storefront_slot_offer_positions (
                  slot_id,
                  position_code,
                  offer_code,
                  position_type,
                  is_featured,
                  sort_order,
                  is_active,
                  visible_from,
                  visible_until
                )
                VALUES (
                  :slot_id,
                  :position_code,
                  :offer_code,
                  'manual',
                  :is_featured,
                  :sort_order,
                  TRUE,
                  NULL,
                  NULL
                )
                """
            ),
            {
                "slot_id": product_grid_slot_id,
                "position_code": offer["position_code"],
                "offer_code": offer["offer_code"],
                "is_featured": offer["sort_order"] == 10,
                "sort_order": offer["sort_order"],
            },
        )

    connection.execute(
        text("DELETE FROM d2c_storefront_slot_items WHERE slot_id = :slot_id"),
        {"slot_id": service_slot_id},
    )

    for item_code, label, sort_order in [
        ("demo-service-fast-shipping", "极速发货", 10),
        ("demo-service-authentic", "正品保障", 20),
        ("demo-service-after-sales", "售后无忧", 30),
    ]:
        connection.execute(
            text(
                """
                INSERT INTO d2c_storefront_slot_items (
                  slot_id,
                  item_code,
                  item_type,
                  label,
                  title,
                  subtitle,
                  description,
                  icon,
                  image_url,
                  link_type,
                  link_value,
                  payload_json,
                  sort_order,
                  is_active
                )
                VALUES (
                  :slot_id,
                  :item_code,
                  'service_promise',
                  :label,
                  NULL,
                  NULL,
                  NULL,
                  NULL,
                  NULL,
                  NULL,
                  NULL,
                  CAST(:payload_json AS json),
                  :sort_order,
                  TRUE
                )
                """
            ),
            {
                "slot_id": service_slot_id,
                "item_code": item_code,
                "label": label,
                "payload_json": _json({"source": "demo_seed"}),
                "sort_order": sort_order,
            },
        )

    connection.execute(
        text(
            """
            UPDATE d2c_storefront_page_slots
            SET content_json = CAST(:content_json AS json),
                presentation_json = CAST(:presentation_json AS json),
                is_active = TRUE
            WHERE id = :slot_id
            """
        ),
        {
            "slot_id": legal_slot_id,
            "content_json": _json(
                {
                    "copyright_text": "© D2C Demo Store",
                    "icp_record_number": "ICP备案号-Demo",
                    "police_record_number": "公安备案号-Demo",
                }
            ),
            "presentation_json": _json({}),
        },
    )


def main() -> None:
    engine = create_engine(_database_url())

    try:
        with engine.begin() as connection:
            _seed_published_catalog(connection)
            _seed_home_config(connection)
    finally:
        engine.dispose()

    print(
        {
            "ok": True,
            "publish_version": DEMO_VERSION,
            "offer_codes": [offer["offer_code"] for offer in DEMO_OFFERS],
        }
    )


if __name__ == "__main__":
    main()
