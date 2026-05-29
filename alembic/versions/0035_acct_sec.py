"""Add storefront account security page."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0035_acct_sec"
down_revision = "0034_pay_result"
branch_labels = None
depends_on = None


ACCOUNT_SECURITY_PAGE = {
    "page_code": "account_security",
    "page_type": "account_security",
    "route_path": "/account/security",
    "title": "账户安全",
    "description": "顾客账户安全与密码管理",
    "seo_title": "账户安全",
    "seo_description": "顾客账户安全与密码管理",
    "auth_required": True,
    "navigation_label": "账户安全",
    "navigation_group": "account",
    "sort_order": 70,
}


def upgrade() -> None:
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
        ACCOUNT_SECURITY_PAGE,
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code = 'account_security'
        """
    )
