"""Add storefront payment result page."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0034_pay_result"
down_revision = "0033_sf_pages"
branch_labels = None
depends_on = None


PAYMENT_RESULT_PAGE = {
    "page_code": "payment_result",
    "page_type": "payment_result",
    "route_path": "/payment-result",
    "title": "支付结果",
    "description": "顾客支付完成结果页",
    "seo_title": "支付结果",
    "seo_description": "顾客支付完成结果页",
    "auth_required": True,
    "navigation_label": "支付结果",
    "navigation_group": "commerce",
    "sort_order": 60,
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
        PAYMENT_RESULT_PAGE,
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM d2c_storefront_pages
        WHERE page_code = 'payment_result'
        """
    )
