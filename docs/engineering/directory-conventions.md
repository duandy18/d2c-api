# d2c-api 目录与命名规范

本文档约束 d2c-api 正式编码阶段的目录、文件命名和模块边界。

当前仓库仍处于独立系统底座阶段，暂不接入 ERP、Gateway、SSO、IAM，也暂不实现商品、购物车、订单业务表。后续扩展业务代码前，必须先确认归属目录，再落文件。

## 一、核心原则

1. 不散放业务代码。
2. 不把临时代码直接写进 app/main.py。
3. 不建立含糊目录，例如 utils、common、misc。
4. 后端目录按职责分层：入口、路由、合同、配置、服务、仓储、模型、集成、投影、测试。
5. 未来接 ERP 时，D2C 作为独立应用接入，不反向污染 ERP。
6. D2C 不拥有 PMS 商品主数据，未来通过 PMS projection 或 read model 使用商品展示数据。
7. D2C 不替代 OMS，未来订单主链路交给 OMS 承接。
8. 第一阶段不提前创建大量空目录，只有当该层真实承担职责时再创建。

## 二、推荐目录

app/
  main.py
  api/
    routes/
  core/
    config.py
  contracts/
  schemas/
  services/
  repos/
  models/
  integrations/
    pms/
    oms/
    erp/
  projections/
    pms/
  health/

tests/
  api/
  services/
  contracts/
  integrations/

scripts/
docs/
  engineering/

## 三、目录职责

app/main.py 只负责创建 FastAPI app、注册路由、中间件和基础配置。禁止写业务逻辑、数据库查询和外部系统调用。

app/api/routes/ 是 HTTP 路由层，只负责请求接收、参数适配、调用 service、返回 response。

app/core/ 是系统基础能力目录，当前已有 config.py，未来可放 database.py、security.py、logging.py。

app/contracts/ 放对外合同、跨系统合同、稳定枚举和未来 ERP 接入合同。

app/schemas/ 放 Pydantic request 和 response schema。

app/services/ 放业务服务层，负责业务规则编排。

app/repos/ 放数据库访问层，负责 SQLAlchemy 查询和持久化。

app/models/ 放 SQLAlchemy ORM model。当前阶段不建业务表。

app/integrations/ 放外部系统集成客户端。未来可能包括 pms、oms、erp。

app/projections/ 放本地投影读模型。未来商品展示数据优先通过 pms projection 进入。

## 四、命名规则

Python 文件使用小写蛇形命名，例如 catalog_service.py、cart_service.py、checkout_service.py、pms_catalog_client.py。

类名使用 PascalCase，例如 CatalogService、CartService、PmsCatalogClient。

函数名使用 snake_case，例如 list_products、create_cart、submit_order_to_oms。

环境变量统一使用 D2C_ 前缀，例如 D2C_ENVIRONMENT、D2C_API_PORT、D2C_DATABASE_URL。

## 五、测试目录规则

测试按被测对象归类：

tests/api/
tests/services/
tests/contracts/
tests/integrations/

当前最小健康检查测试可以暂留 tests/test_health.py。等 API 路由增多后，再迁移到 tests/api/test_health.py。

## 六、ERP 接入预留

固定命名：

app_code = d2c
service_client_code = d2c-service
api_path = /api/d2c
web_path = /d2c
local_api_port = 8025
local_web_port = 5277

未来 ERP 接入逻辑应放在 integrations/erp 或 contracts/erp 相关文件中，禁止写进商城业务 service。

## 七、当前阶段边界

当前阶段允许：

- health
- config
- Makefile
- OpenAPI
- CI
- docs

当前阶段不做：

- 商品表
- 购物车表
- 订单表
- PMS projection 表
- OMS 下单接口
- ERP SSO
- Gateway 配置
- IAM apply / verify
