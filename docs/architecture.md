# 系统架构

## 仓库职责

`frappe-personal` 包含两个边界清晰的部分：

1. `personal/`：安装在 Frappe Bench 中的业务 App。
2. `deploy/`：Personal 生产环境的 Docker 镜像、Compose 和 Nginx 配置。

MCP 协议服务器不在本仓库中维护。它位于独立的
[`frappe-mcp-gateway`](https://github.com/saoxia/frappe-mcp-gateway) 仓库。

## Frappe App 结构

```text
personal/
├── health/
│   ├── doctype/
│   │   ├── health_body_metrics/
│   │   └── health_food_item/
│   ├── body_metrics_service.py
│   └── sidecar_api.py
├── oauth_authorizations.py
├── sidecar_auth.py
├── www/authorized_apps.*
├── hooks.py
└── tests/
```

业务逻辑尽量放在 service 中。DocType controller 负责文档自身校验与派生字段，
MCP API 只负责完成可信身份切换并调用 service，避免形成第二套业务规则。

## 数据所有权

健康 DocType 的权限规则启用 `if_owner`，并在 `hooks.py` 的
`user_data_fields` 中声明 owner 字段。服务层使用正常的 Frappe document API
和 `frappe.get_list`，继承当前用户权限。

因此：

- MCP 调用与 Desk 操作使用相同的数据权限；
- 不能仅凭记录名称读取其他用户数据；
- 导出、报表、打印和删除同样受 owner 约束；
- Guest 不能调用健康业务服务。

## 生产容器

| 服务 | 镜像 | 公开端口 | 持久化 |
| --- | --- | --- | --- |
| `personal` | `personal:runtime` | SSH `22222`；Web/Socket.IO 仅本机 | Bench、站点、文件、日志、环境 |
| `redis` | `redis:7.0-alpine` | `127.0.0.1:6379` | AOF/RDB |
| `nginx` | `nginx:1.26-alpine` | `80`、`443` | 配置、证书、日志 |
| `mcp` | `frappe-mcp-gateway:runtime` | `127.0.0.1:8100` | 环境文件在宿主机 |
| MariaDB | 独立数据库服务 | 不由本 Compose 对公网开放 | 数据库数据目录 |

所有应用服务加入 `personal-network` bridge 网络。对公网只暴露 Nginx 和可选
SSH；Frappe、Redis 和 MCP 的端口只绑定服务器回环地址。

## 持久化原则

Personal 镜像不保存站点数据。以下内容位于宿主机：

- `/srv/pip/frappe-bench`：Bench、apps、sites、上传文件、日志和 Python 环境；
- `/srv/pip/redis/data`：Redis AOF/RDB；
- `/srv/pip/nginx`：Nginx 配置、证书和日志；
- `/srv/pip/frappe-ssh`：`frappe` 用户 SSH 密钥；
- `/srv/pip/ssh-host-keys`：SSH host keys；
- `/srv/pip/mcp.env`：MCP Gateway 配置与断言密钥；
- `/srv/frappe-mcp-gateway`：独立网关代码 checkout。

删除或重建应用容器不会删除这些 bind mount 数据。备份策略仍必须同时覆盖
MariaDB、站点 private/public files、站点配置及密钥。

## 请求路径

### 普通 Web 请求

```text
Browser -> Nginx :443 -> Personal/Frappe :8000 -> MariaDB/Redis
```

### Socket.IO

```text
Browser -> Nginx /socket.io -> Personal :9000
```

### MCP

```text
MCP Client -> Nginx /mcp -> Gateway :8000
           -> Frappe token introspection
           -> Personal internal API + one-time assertion
           -> Frappe permission check -> MariaDB
```

## 依赖方向

`personal` 不依赖 MCP Python SDK。Frappe App 只依赖 `PyJWT` 来验证内部
断言。MCP SDK、HTTP transport 和 token verifier 都由独立 Gateway 管理，
从而避免 MCP SDK 版本限制影响 Frappe 运行时。
