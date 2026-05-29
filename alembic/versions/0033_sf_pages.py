"""Add storefront page surface fields and routes."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0033_sf_pages"
down_revision = "0032_disp_metrics"
branch_labels = None
depends_on = None

PAGE_ROWS = (
    {
        "page_code": "home",
        "page_type": "home",
        "route_path": "/",
        "title": "首页",
        "description": "顾客端首页",
        "seo_title": "首页",
        "seo_description": "顾客端首页",
        "auth_required": False,
        "navigation_label": "首页",
        "navigation_group": "main",
        "sort_order": 10,
    },
    {
        "page_code": "cart",
        "page_type": "cart",
        "route_path": "/cart",
        "title": "购物车",
        "description": "顾客购物车",
        "seo_title": "购物车",
        "seo_description": "顾客购物车",
        "auth_required": False,
        "navigation_label": "购物车",
        "navigation_group": "commerce",
        "sort_order": 20,
    },
    {
        "page_code": "login",
        "page_type": "login",
        "route_path": "/login",
        "title": "登录",
        "description": "顾客登录",
        "seo_title": "登录",
        "seo_description": "顾客登录",
        "auth_required": False,
        "navigation_label": "登录",
        "navigation_group": "account",
        "sort_order": 30,
    },
    {
        "page_code": "register",
        "page_type": "register",
        "route_path": "/register",
        "title": "注册",
        "description": "顾客注册",
        "seo_title": "注册",
        "seo_description": "顾客注册",
        "auth_required": False,
        "navigation_label": "注册",
        "navigation_group": "account",
        "sort_order": 40,
    },
    {
        "page_code": "checkout",
        "page_type": "checkout",
        "route_path": "/checkout",
        "title": "结算",
        "description": "顾客订单结算",
        "seo_title": "结算",
        "seo_description": "顾客订单结算",
        "auth_required": True,
        "navigation_label": "结算",
        "navigation_group": "commerce",
        "sort_order": 50,
    },
)

def upgrade() -> None:
    op.add_column(
        "d2c_storefront_pages",
        sa.Column(
            "auth_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "d2c_storefront_pages",
        sa.Column("navigation_label", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "d2c_storefront_pages",
        sa.Column(
            "navigation_group",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'main'"),
        ),
    )
    op.add_column(
        "d2c_storefront_pages",
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_check_constraint(
        "ck_d2c_sf_pages_route_abs",
        "d2c_storefront_pages",
        "route_path LIKE '/%'",
    )
    op.create_index(
        "ix_d2c_sf_pages_route",
        "d2c_storefront_pages",
        ["site_id", "route_path"],
    )
    op.create_index(
        "ix_d2c_sf_pages_nav",
        "d2c_storefront_pages",
        ["site_id", "navigation_group", "sort_order"],
    )

    bind = op.get_bind()

    for row in PAGE_ROWS:
        bind.execute(
            sa.text(
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
                  seo_description,
                  auth_required,
                  navigation_label,
                  navigation_group,
                  sort_order
                )
                SELECT
                  id,
                  :page_code,
                  :page_type,
                  :route_path,
                  :title,
                  :description,
                  'active',
                  :seo_title,
                  :seo_description,
                  :auth_required,
                  :navigation_label,
                  :navigation_group,
                  :sort_order
                FROM d2c_storefront_sites
                WHERE site_code = 'default'
                ON CONFLICT (site_id, page_code) DO UPDATE SET
                  page_type = EXCLUDED.page_type,
                  route_path = EXCLUDED.route_path,
                  title = EXCLUDED.title,
                  description = EXCLUDED.description,
                  status = EXCLUDED.status,
                  seo_title = EXCLUDED.seo_title,
                  seo_description = EXCLUDED.seo_description,
                  auth_required = EXCLUDED.auth_required,
                  navigation_label = EXCLUDED.navigation_label,
                  navigation_group = EXCLUDED.navigation_group,
                  sort_order = EXCLUDED.sort_order
                """
            ),
            row,
        )

def downgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code IN ('cart', 'login', 'register', 'checkout')
        """
    )

    op.drop_index("ix_d2c_sf_pages_nav", table_name="d2c_storefront_pages")
    op.drop_index("ix_d2c_sf_pages_route", table_name="d2c_storefront_pages")
    op.drop_constraint(
        "ck_d2c_sf_pages_route_abs",
        "d2c_storefront_pages",
        type_="check",
    )
    op.drop_column("d2c_storefront_pages", "sort_order")
    op.drop_column("d2c_storefront_pages", "navigation_group")
    op.drop_column("d2c_storefront_pages", "navigation_label")
    op.drop_column("d2c_storefront_pages", "auth_required")
