"""Keep storefront my center as a single page."""

from __future__ import annotations

from alembic import op

revision = "0037_my_single"
down_revision = "0036_my_center"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code IN ('my_orders', 'my_account', 'my_security')
        """
    )


def downgrade() -> None:
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
          seo_description,
          auth_required,
          navigation_label,
          navigation_group,
          sort_order
        )
        SELECT
          id,
          'my_orders',
          'my_orders',
          '/my/orders',
          '我的购买记录',
          '顾客订单购买记录',
          'active',
          '我的购买记录',
          '顾客订单购买记录',
          true,
          '我的购买记录',
          'account',
          80
        FROM d2c_storefront_sites
        WHERE site_code = 'default'
        ON CONFLICT (site_id, page_code) DO NOTHING
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
          seo_description,
          auth_required,
          navigation_label,
          navigation_group,
          sort_order
        )
        SELECT
          id,
          'my_account',
          'my_account',
          '/my/account',
          '我的账号',
          '顾客账号资料',
          'active',
          '我的账号',
          '顾客账号资料',
          true,
          '我的账号',
          'account',
          90
        FROM d2c_storefront_sites
        WHERE site_code = 'default'
        ON CONFLICT (site_id, page_code) DO NOTHING
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
          seo_description,
          auth_required,
          navigation_label,
          navigation_group,
          sort_order
        )
        SELECT
          id,
          'my_security',
          'my_security',
          '/my/security',
          '账户安全',
          '顾客账户安全与密码管理',
          'active',
          '账户安全',
          '顾客账户安全与密码管理',
          true,
          '账户安全',
          'account',
          100
        FROM d2c_storefront_sites
        WHERE site_code = 'default'
        ON CONFLICT (site_id, page_code) DO NOTHING
        """
    )
