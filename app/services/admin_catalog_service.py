from sqlalchemy.orm import Session

from app.models.catalog import PriceList, Product, ProductCategory, ProductSku, SkuPrice, Unit
from app.repos.admin_catalog_repo import (
    list_price_lists,
    list_product_rows,
    list_sku_price_rows,
    list_sku_rows,
    list_units,
)
from app.schemas.admin_catalog import (
    AdminPriceList,
    AdminPriceListsResponse,
    AdminProduct,
    AdminProductsResponse,
    AdminSku,
    AdminSkuPrice,
    AdminSkuPricesResponse,
    AdminSkusResponse,
    AdminUnit,
    AdminUnitsResponse,
)


def _build_unit(unit: Unit) -> AdminUnit:
    return AdminUnit(
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


def get_admin_units(session: Session) -> AdminUnitsResponse:
    units = [_build_unit(unit) for unit in list_units(session)]
    return AdminUnitsResponse(count=len(units), units=units)


def _build_price_list(price_list: PriceList) -> AdminPriceList:
    return AdminPriceList(
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


def get_admin_price_lists(session: Session) -> AdminPriceListsResponse:
    price_lists = [_build_price_list(price_list) for price_list in list_price_lists(session)]
    return AdminPriceListsResponse(
        count=len(price_lists),
        price_lists=price_lists,
    )


def _build_product(product: Product, category: ProductCategory) -> AdminProduct:
    return AdminProduct(
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


def get_admin_products(session: Session) -> AdminProductsResponse:
    products = [
        _build_product(product, category) for product, category in list_product_rows(session)
    ]
    return AdminProductsResponse(count=len(products), products=products)


def _build_sku(
    sku: ProductSku,
    product: Product,
    unit: Unit,
    storefront_price: SkuPrice | None,
) -> AdminSku:
    return AdminSku(
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


def get_admin_skus(session: Session) -> AdminSkusResponse:
    skus = [
        _build_sku(sku, product, unit, storefront_price)
        for sku, product, unit, storefront_price in list_sku_rows(session)
    ]
    return AdminSkusResponse(count=len(skus), skus=skus)


def _build_sku_price(
    sku_price: SkuPrice,
    price_list: PriceList,
    sku: ProductSku,
    product: Product,
) -> AdminSkuPrice:
    return AdminSkuPrice(
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


def get_admin_sku_prices(session: Session) -> AdminSkuPricesResponse:
    sku_prices = [
        _build_sku_price(sku_price, price_list, sku, product)
        for sku_price, price_list, sku, product in list_sku_price_rows(session)
    ]
    return AdminSkuPricesResponse(
        count=len(sku_prices),
        sku_prices=sku_prices,
    )
