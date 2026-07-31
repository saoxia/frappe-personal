# 开发与测试

## 环境要求

- Python `>=3.14,<3.15`
- Frappe `>=16.0.0-dev,<18.0.0`
- Flow `>=0.0.1,<1.0.0`
- Node.js 与 Yarn/pnpm 由 Bench 环境提供

本仓库是现有 Frappe App。不要再次执行 `bench new-app`。

## 本地安装

```sh
cd /path/to/frappe-bench
bench get-app https://github.com/saoxia/frappe-personal.git
bench --site development.localhost install-app personal
bench --site development.localhost migrate
bench build --app personal
```

`personal/hooks.py` 声明 `flow` 为 required app，安装 Personal 前应先安装
Flow。

## 常用命令

所有 Bench 命令都应明确指定站点：

```sh
bench --site development.localhost list-apps
bench --site development.localhost migrate
bench --site development.localhost clear-cache
bench build --app personal
```

## 测试

完整测试：

```sh
bench --site development.localhost run-tests --app personal
```

按模块测试：

```sh
bench --site development.localhost run-tests \
  --module personal.health.test_body_metrics_service

bench --site development.localhost run-tests \
  --module personal.health.test_sidecar_api

bench --site development.localhost run-tests \
  --module personal.tests.test_oauth_authorizations
```

不要在生产站点运行自动化测试。测试会创建用户、OAuth token 和业务记录。

## 代码组织约定

- DocType 自身字段校验和派生值放在 controller。
- 可复用业务流程放在 `*_service.py`。
- Whitelisted method 保持小而明确，不复制 service 逻辑。
- 权限检查使用 Frappe document/query API，不绕过 owner 或角色权限。
- MCP 内部入口必须先通过 `authenticated_sidecar_user()`。
- 写入接口接受 `client_request_id` 时，服务端负责真正的幂等约束。
- 用户可见字符串使用 `frappe._()` 并更新 gettext 翻译。

## 增加 DocType

在开发站点和 developer mode 下通过 Frappe 创建或修改 DocType，然后提交
导出的 JSON、controller、测试和翻译。更改字段后运行：

```sh
bench --site development.localhost migrate
bench --site development.localhost run-tests --app personal
```

## 增加 MCP 工具

一个新 MCP 能力通常同时修改两个仓库：

1. Personal 中增加明确的 service 和内部业务 API。
2. `frappe-mcp-gateway` 中注册面向客户端的 MCP tool。

Personal 侧必须先完成权限、参数、幂等和审计设计。Gateway 不能调用任意
method，也不能绕过 Personal 的业务规则。

## 提交前检查

```sh
git diff --check
bench --site development.localhost run-tests --app personal
```

涉及部署文件时，还应运行：

```sh
docker compose -f deploy/docker-compose.yml config --quiet
```
