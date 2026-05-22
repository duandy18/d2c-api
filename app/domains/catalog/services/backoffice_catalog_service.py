"""Backoffice catalog service."""

from sqlalchemy.orm import Session

from app.domains.catalog.contracts.backoffice_catalog_contract import (
    BackofficePriceList,
    BackofficePriceListsResponse,
    BackofficeProduct,
    BackofficeProductsResponse,
    BackofficeSku,
    BackofficeSkuPrice,
    BackofficeSkuPricesResponse,
    BackofficeSkusResponse,
    BackofficeUnit,
    BackofficeUnitsResponse,
)
from app.domains.catalog.models.catalog import (
    PriceList,
    Product,
    ProductCategory,
    ProductSku,
    SkuPrice,
    Unit,
)
from app.domains.catalog.repos.backoffice_catalog_repo import (
    list_price_lists,
    list_product_rows,
    list_sku_price_rows,
    list_sku_rows,
    list_units,
)


def _build_unit(unit: Unit) -> BackofficeUnit:
    return BackofficeUnit(
        id=unit.id,
        unit_code=unit.unit_code,
        name=unit.name,
        unit_type=unit.unit_type,
        symbol=unit.symbol,
        precision=unit.precision,
        is_base_unit=unit.is_base_unit,
        base_unit_code=unit.base_unit_code,
        conversion_factor=unit.conversion_factor,
        is_active=unit.is_active,
        sort_order=unit.sort_order,
        created_at=unit.created_at,
        updated_at=unit.updated_at,
    )


def get_backoffice_units(session: Session) -> BackofficeUnitsResponse:
    units = [_build_unit(unit) for unit in list_units(session)]
    return BackofficeUnitsResponse(count=len(units), units=units)


def _build_price_list(price_list: PriceList) -> BackofficePriceList:
    return BackofficePriceList(
        id=price_list.id,
        price_list_code=price_list.price_list_code,
        name=price_list.name,
        currency=price_list.currency,
        region_code=price_list.region_code,
        channel=price_list.channel,
        customer_segment=price_list.customer_segment,
        priority=price_list.priority,
        is_default=price_list.is_default,
        is_active=price_list.is_active,
        effective_from=price_list.effective_from,
        effective_to=price_list.effective_to,
        created_at=price_list.created_at,
        updated_at=price_list.updated_at,
    )


def get_backoffice_price_lists(session: Session) -> BackofficePriceListsResponse:
    price_lists = [_build_price_list(price_list) for price_list in list_price_lists(session)]
    return BackofficePriceListsResponse(
        count=len(price_lists),
        price_lists=price_lists,
    )


def _build_product(product: Product, category: ProductCategory) -> BackofficeProduct:
    return BackofficeProduct(
        id=product.id,
        product_code=product.product_code,
        name=product.name,
        subtitle=product.subtitle,
        description=product.description,
        category_id=product.category_id,
        category_code=category.code,
        category_name=category.name,
        status=product.status,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def get_backoffice_products(session: Session) -> BackofficeProductsResponse:
    products = [
        _build_product(product, category) for product, category in list_product_rows(session)
    ]
    return BackofficeProductsResponse(count=len(products), products=products)


def _build_sku(
    sku: ProductSku,
    product: Product,
    unit: Unit,
    storefront_price: SkuPrice | None,
) -> BackofficeSku:
    return BackofficeSku(
        id=sku.id,
        product_id=sku.product_id,
        product_code=product.product_code,
        sku_code=sku.sku_code,
        name=sku.name,
        legacy_price_cents=sku.price_cents,
        legacy_currency=sku.currency,
        storefront_price_cents=(
            storefront_price.price_cents if storefront_price is not None else None
        ),
        storefront_currency=(storefront_price.currency if storefront_price is not None else None),
        stock_status=sku.stock_status,
        image_url=sku.image_url,
        sales_unit_id=sku.sales_unit_id,
        sales_unit_code=unit.unit_code,
        sales_unit_name=unit.name,
        package_quantity=sku.package_quantity,
        package_unit_text=sku.package_unit_text,
        is_active=sku.is_active,
        sort_order=sku.sort_order,
        created_at=sku.created_at,
        updated_at=sku.updated_at,
    )


def get_backoffice_skus(session: Session) -> BackofficeSkusResponse:
    skus = [
        _build_sku(sku, product, unit, storefront_price)
        for sku, product, unit, storefront_price in list_sku_rows(session)
    ]
    return BackofficeSkusResponse(count=len(skus), skus=skus)


def _build_sku_price(
    sku_price: SkuPrice,
    price_list: PriceList,
    sku: ProductSku,
    product: Product,
) -> BackofficeSkuPrice:
    return BackofficeSkuPrice(
        id=sku_price.id,
        price_list_id=sku_price.price_list_id,
        price_list_code=price_list.price_list_code,
        price_list_name=price_list.name,
        channel=price_list.channel,
        customer_segment=price_list.customer_segment,
        sku_id=sku_price.sku_id,
        sku_code=sku.sku_code,
        product_id=product.id,
        product_code=product.product_code,
        price_cents=sku_price.price_cents,
        compare_at_price_cents=sku_price.compare_at_price_cents,
        currency=sku_price.currency,
        effective_from=sku_price.effective_from,
        effective_to=sku_price.effective_to,
        is_active=sku_price.is_active,
        created_at=sku_price.created_at,
        updated_at=sku_price.updated_at,
    )


def get_backoffice_sku_prices(session: Session) -> BackofficeSkuPricesResponse:
    sku_prices = [
        _build_sku_price(sku_price, price_list, sku, product)
        for sku_price, price_list, sku, product in list_sku_price_rows(session)
    ]
    return BackofficeSkuPricesResponse(
        count=len(sku_prices),
        sku_prices=sku_prices,
    )
