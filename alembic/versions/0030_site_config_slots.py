"""add slot first storefront site config

Revision ID: 0030_site_config
Revises: 0029_client_pres_rt
Create Date: 2026-05-28 23:59:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0030_site_config"
down_revision: str | Sequence[str] | None = "0029_client_pres_rt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "d2c_storefront_sites",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("site_code", sa.String(length=64), nullable=False),
        sa.Column("site_name", sa.String(length=160), nullable=False),
        sa.Column("brand_name", sa.String(length=160), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("default_currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("site_code", name="uq_d2c_sf_sites_code"),
        sa.CheckConstraint(
            "status IN ('active', 'disabled')",
            name="ck_d2c_sf_sites_status",
        ),
    )
    op.create_index("ix_d2c_sf_sites_status", "d2c_storefront_sites", ["status"])

    op.create_table(
        "d2c_storefront_theme_settings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("site_id", sa.BigInteger(), nullable=False),
        sa.Column("theme_code", sa.String(length=64), nullable=False),
        sa.Column("primary_color", sa.String(length=32), nullable=False),
        sa.Column("secondary_color", sa.String(length=32), nullable=False),
        sa.Column("background_color", sa.String(length=32), nullable=False),
        sa.Column("text_color", sa.String(length=32), nullable=False),
        sa.Column("font_family", sa.String(length=160), nullable=True),
        sa.Column("corner_radius", sa.String(length=32), nullable=False, server_default="24px"),
        sa.Column("button_style", sa.String(length=32), nullable=False, server_default="pill"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["d2c_storefront_sites.id"],
            name="fk_d2c_sf_theme_site",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("site_id", "theme_code", name="uq_d2c_sf_theme_code"),
    )
    op.create_index(
        "ix_d2c_sf_theme_active",
        "d2c_storefront_theme_settings",
        ["site_id", "is_active"],
    )

    op.create_table(
        "d2c_storefront_pages",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("site_id", sa.BigInteger(), nullable=False),
        sa.Column("page_code", sa.String(length=64), nullable=False),
        sa.Column("page_type", sa.String(length=32), nullable=False),
        sa.Column("route_path", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("seo_title", sa.String(length=180), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["d2c_storefront_sites.id"],
            name="fk_d2c_sf_pages_site",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("site_id", "page_code", name="uq_d2c_sf_pages_code"),
        sa.CheckConstraint(
            "status IN ('active', 'disabled')",
            name="ck_d2c_sf_pages_status",
        ),
    )
    op.create_index(
        "ix_d2c_sf_pages_status",
        "d2c_storefront_pages",
        ["site_id", "status"],
    )

    op.create_table(
        "d2c_storefront_page_slots",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("page_id", sa.BigInteger(), nullable=False),
        sa.Column("slot_code", sa.String(length=96), nullable=False),
        sa.Column("slot_type", sa.String(length=64), nullable=False),
        sa.Column("slot_group", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("subtitle", sa.String(length=240), nullable=True),
        sa.Column(
            "content_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column(
            "presentation_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["d2c_storefront_pages.id"],
            name="fk_d2c_sf_slots_page",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("page_id", "slot_code", name="uq_d2c_sf_slots_code"),
        sa.CheckConstraint("sort_order >= 0", name="ck_d2c_sf_slots_sort_nonneg"),
    )
    op.create_index(
        "ix_d2c_sf_slots_order",
        "d2c_storefront_page_slots",
        ["page_id", "sort_order", "slot_code"],
    )
    op.create_index(
        "ix_d2c_sf_slots_active",
        "d2c_storefront_page_slots",
        ["page_id", "is_active"],
    )

    op.create_table(
        "d2c_storefront_slot_items",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("slot_id", sa.BigInteger(), nullable=False),
        sa.Column("item_code", sa.String(length=96), nullable=False),
        sa.Column("item_type", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("subtitle", sa.String(length=240), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("link_type", sa.String(length=32), nullable=True),
        sa.Column("link_value", sa.String(length=240), nullable=True),
        sa.Column(
            "payload_json",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["d2c_storefront_page_slots.id"],
            name="fk_d2c_sf_slot_items_slot",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("slot_id", "item_code", name="uq_d2c_sf_slot_items_code"),
        sa.CheckConstraint(
            "sort_order >= 0",
            name="ck_d2c_sf_slot_items_sort_nonneg",
        ),
    )
    op.create_index(
        "ix_d2c_sf_slot_items_order",
        "d2c_storefront_slot_items",
        ["slot_id", "sort_order", "item_code"],
    )
    op.create_index(
        "ix_d2c_sf_slot_items_active",
        "d2c_storefront_slot_items",
        ["slot_id", "is_active"],
    )

    op.create_table(
        "d2c_storefront_slot_offer_positions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("slot_id", sa.BigInteger(), nullable=False),
        sa.Column("position_code", sa.String(length=96), nullable=False),
        sa.Column("offer_code", sa.String(length=96), nullable=False),
        sa.Column("position_type", sa.String(length=64), nullable=False, server_default="manual"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("visible_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["d2c_storefront_page_slots.id"],
            name="fk_d2c_sf_slot_offer_pos_slot",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "slot_id",
            "position_code",
            name="uq_d2c_sf_slot_offer_pos_code",
        ),
        sa.UniqueConstraint(
            "slot_id",
            "offer_code",
            name="uq_d2c_sf_slot_offer_pos_offer",
        ),
        sa.CheckConstraint(
            "sort_order >= 0",
            name="ck_d2c_sf_slot_offer_pos_sort_nonneg",
        ),
        sa.CheckConstraint(
            "visible_until IS NULL OR visible_from IS NULL OR visible_until > visible_from",
            name="ck_d2c_sf_slot_offer_pos_window",
        ),
    )
    op.create_index(
        "ix_d2c_sf_slot_offer_pos_order",
        "d2c_storefront_slot_offer_positions",
        ["slot_id", "sort_order", "position_code"],
    )
    op.create_index(
        "ix_d2c_sf_slot_offer_pos_offer",
        "d2c_storefront_slot_offer_positions",
        ["offer_code"],
    )
    op.create_index(
        "ix_d2c_sf_slot_offer_pos_active",
        "d2c_storefront_slot_offer_positions",
        ["slot_id", "is_active"],
    )

    _seed_default_home()


def downgrade() -> None:
    op.drop_index(
        "ix_d2c_sf_slot_offer_pos_active",
        table_name="d2c_storefront_slot_offer_positions",
    )
    op.drop_index(
        "ix_d2c_sf_slot_offer_pos_offer",
        table_name="d2c_storefront_slot_offer_positions",
    )
    op.drop_index(
        "ix_d2c_sf_slot_offer_pos_order",
        table_name="d2c_storefront_slot_offer_positions",
    )
    op.drop_table("d2c_storefront_slot_offer_positions")

    op.drop_index("ix_d2c_sf_slot_items_active", table_name="d2c_storefront_slot_items")
    op.drop_index("ix_d2c_sf_slot_items_order", table_name="d2c_storefront_slot_items")
    op.drop_table("d2c_storefront_slot_items")

    op.drop_index("ix_d2c_sf_slots_active", table_name="d2c_storefront_page_slots")
    op.drop_index("ix_d2c_sf_slots_order", table_name="d2c_storefront_page_slots")
    op.drop_table("d2c_storefront_page_slots")

    op.drop_index("ix_d2c_sf_pages_status", table_name="d2c_storefront_pages")
    op.drop_table("d2c_storefront_pages")

    op.drop_index("ix_d2c_sf_theme_active", table_name="d2c_storefront_theme_settings")
    op.drop_table("d2c_storefront_theme_settings")

    op.drop_index("ix_d2c_sf_sites_status", table_name="d2c_storefront_sites")
    op.drop_table("d2c_storefront_sites")


def _seed_default_home() -> None:
    op.execute(
        """
        INSERT INTO d2c_storefront_sites (
          site_code, site_name, brand_name, status, default_currency
        )
        VALUES ('default', 'D2C 默认独立站', 'Paw Home', 'active', 'USD')
        ON CONFLICT (site_code) DO UPDATE
        SET
          site_name = EXCLUDED.site_name,
          brand_name = EXCLUDED.brand_name,
          status = EXCLUDED.status,
          default_currency = EXCLUDED.default_currency,
          updated_at = now()
        """
    )

    op.execute(
        """
        INSERT INTO d2c_storefront_theme_settings (
          site_id,
          theme_code,
          primary_color,
          secondary_color,
          background_color,
          text_color,
          font_family,
          corner_radius,
          button_style,
          is_active
        )
        SELECT
          id,
          'default',
          '#201713',
          '#8a3f1f',
          '#fff7ee',
          '#201713',
          'system-ui',
          '24px',
          'pill',
          TRUE
        FROM d2c_storefront_sites
        WHERE site_code = 'default'
        ON CONFLICT (site_id, theme_code) DO UPDATE
        SET
          primary_color = EXCLUDED.primary_color,
          secondary_color = EXCLUDED.secondary_color,
          background_color = EXCLUDED.background_color,
          text_color = EXCLUDED.text_color,
          font_family = EXCLUDED.font_family,
          corner_radius = EXCLUDED.corner_radius,
          button_style = EXCLUDED.button_style,
          is_active = EXCLUDED.is_active,
          updated_at = now()
        """
    )

    op.execute(
        """
        INSERT INTO d2c_storefront_pages (
          site_id,
          page_code,
          page_type,
          route_path,
          title,
          description,
          status,
          seo_title,
          seo_description
        )
        SELECT
          id,
          'home',
          'home',
          '/',
          '首页',
          'D2C 独立站首页',
          'active',
          'Paw Home 独立商城',
          '精选猫用品独立商城'
        FROM d2c_storefront_sites
        WHERE site_code = 'default'
        ON CONFLICT (site_id, page_code) DO UPDATE
        SET
          page_type = EXCLUDED.page_type,
          route_path = EXCLUDED.route_path,
          title = EXCLUDED.title,
          description = EXCLUDED.description,
          status = EXCLUDED.status,
          seo_title = EXCLUDED.seo_title,
          seo_description = EXCLUDED.seo_description,
          updated_at = now()
        """
    )

    op.execute(
        """
        WITH home_page AS (
          SELECT p.id AS page_id
          FROM d2c_storefront_pages p
          JOIN d2c_storefront_sites s ON s.id = p.site_id
          WHERE s.site_code = 'default' AND p.page_code = 'home'
        )
        INSERT INTO d2c_storefront_page_slots (
          page_id,
          slot_code,
          slot_type,
          slot_group,
          title,
          subtitle,
          content_json,
          presentation_json,
          sort_order,
          is_active
        )
        SELECT page_id, slot_code, slot_type, slot_group, title, subtitle,
               content_json::json, '{}'::json, sort_order, TRUE
        FROM home_page,
        (
          VALUES
            (
              'header.brand',
              'brand',
              'header',
              '品牌名称',
              NULL,
              '{"brand_name":"Paw Home"}',
              10
            ),
            (
              'header.login_link',
              'login_link',
              'header',
              '登录入口',
              NULL,
              '{"label":"登录","link_target":"#login"}',
              20
            ),
            (
              'product_collection.tabs',
              'collection_tabs',
              'navigation',
              '商品集合导航',
              NULL,
              '{"title":"商品集合"}',
              30
            ),
            (
              'hero.title',
              'hero',
              'main',
              '首页标题',
              '首页首屏标题',
              '{"kicker":"精选好物","title":"猫用品精选商城"}',
              40
            ),
            (
              'campaign.banner',
              'campaign_banner',
              'main',
              '首页广告位',
              NULL,
              '{"label":"限时活动","title":"满 99 减 20","subtitle":"猫粮猫砂组合优惠"}',
              50
            ),
            (
              'product_category.nav',
              'category_nav',
              'navigation',
              '商品分类导航',
              NULL,
              '{"title":"商品分类"}',
              60
            ),
            (
              'cart.entry',
              'cart_entry',
              'navigation',
              '购物车入口',
              NULL,
              '{"label":"购物车","link_target":"#cart"}',
              70
            ),
            (
              'product_grid.list',
              'product_grid',
              'commerce',
              '热卖商品',
              '只保存 offer_code，运行时由 d2c-api hydrate 商品事实',
              '{"title":"热卖商品","subtitle":"真实上架商品与真实价格"}',
              80
            ),
            (
              'service.promise_bar',
              'service_promise_bar',
              'footer',
              '服务承诺',
              NULL,
              '{"title":"服务承诺"}',
              90
            ),
            (
              'site.legal_footer',
              'legal_footer',
              'footer',
              '页脚备案',
              NULL,
              '{"copyright_text":"© Paw Home","icp_record_number":"","police_record_number":""}',
              100
            )
        ) AS rows(
          slot_code,
          slot_type,
          slot_group,
          title,
          subtitle,
          content_json,
          sort_order
        )
        ON CONFLICT (page_id, slot_code) DO UPDATE
        SET
          slot_type = EXCLUDED.slot_type,
          slot_group = EXCLUDED.slot_group,
          title = EXCLUDED.title,
          subtitle = EXCLUDED.subtitle,
          content_json = EXCLUDED.content_json,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active,
          updated_at = now()
        """
    )

    op.execute(
        """
        WITH slots AS (
          SELECT ps.id AS slot_id, ps.slot_code
          FROM d2c_storefront_page_slots ps
          JOIN d2c_storefront_pages p ON p.id = ps.page_id
          JOIN d2c_storefront_sites s ON s.id = p.site_id
          WHERE s.site_code = 'default' AND p.page_code = 'home'
        )
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
        SELECT
          slots.slot_id,
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
          '{}'::json,
          sort_order,
          TRUE
        FROM slots
        JOIN (
          VALUES
            ('product_collection.tabs','all','collection','全部商品',NULL,NULL,NULL,NULL,NULL,'anchor','#products',10),
            ('product_collection.tabs','new','collection','新品',NULL,NULL,NULL,NULL,NULL,'anchor','#products',20),
            ('product_collection.tabs','hot','collection','热卖',NULL,NULL,NULL,NULL,NULL,'anchor','#products',30),
            ('product_collection.tabs','recommend','collection','推荐',NULL,NULL,NULL,NULL,NULL,'anchor','#products',40),
            ('product_category.nav','cat_food','category','猫粮',NULL,NULL,NULL,NULL,NULL,'anchor','#products',10),
            ('product_category.nav','cat_litter','category','猫砂',NULL,NULL,NULL,NULL,NULL,'anchor','#products',20),
            ('product_category.nav','cat_treat','category','猫零食',NULL,NULL,NULL,NULL,NULL,'anchor','#products',30),
            ('service.promise_bar','authentic','service','正品保障',NULL,NULL,NULL,'shield',NULL,NULL,NULL,10),
            ('service.promise_bar','fast_shipping','service','快速发货',NULL,NULL,NULL,'truck',NULL,NULL,NULL,20),
            ('service.promise_bar','after_sales','service','售后无忧',NULL,NULL,NULL,'heart',NULL,NULL,NULL,30)
        ) AS rows(
          slot_code,
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
          sort_order
        )
        ON rows.slot_code = slots.slot_code
        ON CONFLICT (slot_id, item_code) DO UPDATE
        SET
          item_type = EXCLUDED.item_type,
          label = EXCLUDED.label,
          title = EXCLUDED.title,
          subtitle = EXCLUDED.subtitle,
          description = EXCLUDED.description,
          icon = EXCLUDED.icon,
          image_url = EXCLUDED.image_url,
          link_type = EXCLUDED.link_type,
          link_value = EXCLUDED.link_value,
          payload_json = EXCLUDED.payload_json,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active,
          updated_at = now()
        """
    )

    op.execute(
        """
        WITH product_slot AS (
          SELECT ps.id AS slot_id
          FROM d2c_storefront_page_slots ps
          JOIN d2c_storefront_pages p ON p.id = ps.page_id
          JOIN d2c_storefront_sites s ON s.id = p.site_id
          WHERE s.site_code = 'default'
            AND p.page_code = 'home'
            AND ps.slot_code = 'product_grid.list'
        )
        INSERT INTO d2c_storefront_slot_offer_positions (
          slot_id,
          position_code,
          offer_code,
          position_type,
          is_featured,
          sort_order,
          is_active
        )
        SELECT slot_id, position_code, offer_code, 'manual', is_featured, sort_order, TRUE
        FROM product_slot,
        (
          VALUES
            ('home-product-grid-001', 'offer.cat_litter.tofu_6l', TRUE, 10),
            ('home-product-grid-002', 'offer-cat-food-salmon-001', FALSE, 20)
        ) AS rows(position_code, offer_code, is_featured, sort_order)
        ON CONFLICT (slot_id, position_code) DO UPDATE
        SET
          offer_code = EXCLUDED.offer_code,
          position_type = EXCLUDED.position_type,
          is_featured = EXCLUDED.is_featured,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active,
          updated_at = now()
        """
    )
