from app.schemas.catalog import CatalogProduct, CatalogProductsResponse

PLACEHOLDER_PRODUCTS: tuple[CatalogProduct, ...] = (
    CatalogProduct(
        product_id="pet-cat-food-salmon-001",
        sku="CAT-FOOD-SALMON-1KG",
        name="三文鱼成猫粮 1kg",
        category="猫粮",
        description="面向成猫的三文鱼风味日常主粮，占位商品，未来来自 PMS projection。",
        price_cents=1899,
        tags=["猫粮", "成猫", "精选"],
        stock_status="in_stock",
    ),
    CatalogProduct(
        product_id="pet-cat-litter-tofu-001",
        sku="CAT-LITTER-TOFU-6L",
        name="豆腐猫砂 6L",
        category="猫砂",
        description="低尘豆腐猫砂，占位商品，未来来自 PMS projection。",
        price_cents=1299,
        tags=["猫砂", "低尘", "可冲散"],
        stock_status="in_stock",
    ),
    CatalogProduct(
        product_id="pet-cat-treat-chicken-001",
        sku="CAT-TREAT-CHICKEN-80G",
        name="鸡肉冻干零食 80g",
        category="零食",
        description="鸡肉冻干宠物零食，占位商品，未来来自 PMS projection。",
        price_cents=999,
        tags=["零食", "冻干", "高蛋白"],
        stock_status="low_stock",
    ),
    CatalogProduct(
        product_id="pet-cat-toy-feather-001",
        sku="CAT-TOY-FEATHER",
        name="羽毛逗猫棒",
        category="玩具",
        description="互动逗猫玩具，占位商品，未来来自 PMS projection。",
        price_cents=699,
        tags=["玩具", "互动", "新手养猫"],
        stock_status="in_stock",
    ),
    CatalogProduct(
        product_id="pet-care-wipes-001",
        sku="PET-CARE-WIPES-80",
        name="宠物清洁湿巾 80片",
        category="护理用品",
        description="宠物日常清洁湿巾，占位商品，未来来自 PMS projection。",
        price_cents=799,
        tags=["护理", "清洁", "日用品"],
        stock_status="in_stock",
    ),
    CatalogProduct(
        product_id="pet-travel-bowl-001",
        sku="PET-TRAVEL-BOWL",
        name="便携折叠食盆",
        category="出行与日用品",
        description="适合外出携带的宠物折叠食盆，占位商品，未来来自 PMS projection。",
        price_cents=599,
        tags=["出行", "日用品", "便携"],
        stock_status="out_of_stock",
    ),
)


def list_catalog_products() -> CatalogProductsResponse:
    products = list(PLACEHOLDER_PRODUCTS)
    return CatalogProductsResponse(count=len(products), products=products)


def get_catalog_product(product_id: str) -> CatalogProduct | None:
    for product in PLACEHOLDER_PRODUCTS:
        if product.product_id == product_id:
            return product

    return None
