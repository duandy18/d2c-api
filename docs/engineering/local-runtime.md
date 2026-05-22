# d2c-api 本地运行说明

本文档记录 d2c-api 当前阶段的本地运行方式。

当前阶段只验证独立 API 底座，不接 ERP、Gateway、SSO、IAM，不接数据库业务表。

## 一、固定约定

app_code = d2c
service_client_code = d2c-service
api_path = /api/d2c
web_path = /d2c
local_api_port = 8025
local_web_port = 5277

## 二、本地安装

在 d2c-api 仓库执行：

make install

## 三、本地检查

在 d2c-api 仓库执行：

make check

也可以单独运行测试：

make test

或指定测试文件 / 测试目录：

make test TESTS=tests/test_health.py
make test TESTS=tests

该命令包含：

- ruff check
- pytest
- routes
- openapi export

## 四、本地启动 API

前台开发启动：

make uvicorn

后台启动：

make uvicorn-up

停止后台进程：

make uvicorn-down

重启后台进程：

make uvicorn-restart

查看当前状态：

make uvicorn-status

查看日志：

make uvicorn-logs

同时保留短别名：

make up
make down
make restart
make status
make logs

默认监听：

http://127.0.0.1:8025

健康检查地址：

http://127.0.0.1:8025/health

## 五、后台运行约定

后台运行固定使用：

PID 文件：/tmp/d2c_api_8025.pid
日志文件：/tmp/d2c_api_8025.log

不要使用时间戳日志名，避免 /tmp 堆积。

## 六、日志文件建议

本地调试日志固定使用：

/tmp/d2c_api_8025.log

不要使用时间戳日志名，避免 /tmp 堆积。

## 七、当前阶段边界

当前阶段允许：

- health route
- config
- route listing
- openapi export
- local uvicorn

当前阶段不做：

- 数据库业务表
- 商品接口
- 购物车接口
- 订单接口
- ERP SSO
- Gateway 接入
- IAM apply / verify
