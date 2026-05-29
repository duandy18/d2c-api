"""Add storefront my center pages."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0036_my_center"
down_revision = "0035_acct_sec"
branch_labels = None
depends_on = None


MY_CENTER_PAGES = (
    {
        "page_code": "my_home",
        "page_type": "my_home",
        "route_path": "/my",
        "title": "我的",
        "description": "顾客个人中心",
        "seo_title": "我的",
        "seo_description": "顾客个人中心",
        "auth_required": True,
        "navigation_label": "我的",
        "navigation_group": "account",
        "sort_order": 70,
    },
    {
        "page_code": "my_orders",
        "page_type": "my_orders",
        "route_path": "/my/orders",
        "title": "我的购买记录",
        "description": "顾客订单购买记录",
        "seo_title": "我的购买记录",
        "seo_description": "顾客订单购买记录",
        "auth_required": True,
        "navigation_label": "我的购买记录",
        "navigation_group": "account",
        "sort_order": 80,
    },
    {
        "page_code": "my_account",
        "page_type": "my_account",
        "route_path": "/my/account",
        "title": "我的账号",
        "description": "顾客账号资料",
        "seo_title": "我的账号",
        "seo_description": "顾客账号资料",
        "auth_required": True,
        "navigation_label": "我的账号",
        "navigation_group": "account",
        "sort_order": 90,
    },
    {
        "page_code": "my_security",
        "page_type": "my_security",
        "route_path": "/my/security",
        "title": "账户安全",
        "description": "顾客账户安全与密码管理",
        "seo_title": "账户安全",
        "seo_description": "顾客账户安全与密码管理",
        "auth_required": True,
        "navigation_label": "账户安全",
        "navigation_group": "account",
        "sort_order": 100,
    },
)


def _upsert_pages() -> None:
    bind = op.get_bind()

    for row in MY_CENTER_PAGES:
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


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code = 'account_security'
        """
    )
    _upsert_pages()


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code IN ('my_home', 'my_orders', 'my_account', 'my_security')
        """
    )

    bind = op.get_bind()
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
              'account_security',
              'account_security',
              '/account/security',
              '账户安全',
              '顾客账户安全与密码管理',
              'active',
              '账户安全',
              '顾客账户安全与密码管理',
              true,
              '账户安全',
              'account',
              70
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
        )
    )
