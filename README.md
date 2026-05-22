# d2c-api

D2C 自有商城后端服务。

## 定位

`d2c-api` 是 D2C 自有商城独立系统的后端仓库。

当前第一阶段只建立独立服务底座，暂不接入 ERP、Gateway、SSO、IAM、商品、购物车、订单等业务模块。

## 预留约定

- app_code: `d2c`
- service_client_code: `d2c-service`
- api_path: `/api/d2c`
- web_path: `/d2c`
- local api port: `8025`
- local web port: `5177`
- local database: `postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c`

## 当前阶段

Step 1:

- 创建 GitHub 仓库
- 创建本地目录
- 初始化 git
- 写入 `.gitignore`
- 写入 `README.md`

## Local startup

D2C API backend local standard:

    make uvicorn-up
    make uvicorn-status
    make uvicorn-logs
    make uvicorn-restart
    make uvicorn-down

Default API port: 8025.

Do not use `make dev` as the backend standard startup command.
