# OAuth 与 MCP 集成

## 职责划分

Frappe 是 Authorization Server 和用户身份来源。
[`frappe-mcp-gateway`](https://github.com/saoxia/frappe-mcp-gateway) 是
OAuth Resource Server 与 MCP transport。Personal 提供最终业务 API。

不需要增加另一套身份验证系统。

## 授权流程

1. 用户在 MCP 客户端中添加 Personal 的 MCP URL。
2. 客户端通过 OAuth metadata 找到 Frappe 授权端点。
3. 用户登录 Frappe，并允许 `openid` 和 `personal:mcp` scope。
4. 客户端携带 Frappe access token 调用 Gateway。
5. Gateway 每次请求都调用 Frappe `introspect_token`。
6. Gateway 将已验证用户写入一个 60 秒有效的内部断言。
7. Personal 验证断言，以 `sub` 用户身份执行白名单业务 API。

OAuth access token 不会被转发给 Personal 的业务 method。

## 内部断言

Personal 默认要求：

| 配置 | 默认值 |
| --- | --- |
| Header | `X-Personal-MCP-Assertion` |
| Issuer | `personal-mcp-sidecar` |
| Audience | `personal-frappe-api` |
| Scope | `personal:mcp` |
| Algorithm | `HS256` |

站点配置必须包含至少 32 字符的 `mcp_assertion_secret`。可选配置：

```json
{
  "mcp_assertion_secret": "replace-with-a-random-secret",
  "mcp_assertion_issuer": "personal-mcp-sidecar",
  "mcp_assertion_audience": "personal-frappe-api",
  "mcp_required_scope": "personal:mcp"
}
```

实际密钥不能提交到 Git。

Personal 校验以下 claims：

- `sub`：启用中的 Frappe 用户；
- `iss`、`aud`：与站点配置一致；
- `iat`、`exp`：签发和过期时间；
- `jti`：一次性请求标识；
- `scope`：包含 `personal:mcp`。

`jti` 会通过共享 Redis cache 原子登记，到期前第二次使用同一断言会被拒绝。

## 用户撤销授权

登录用户访问：

```text
/authorized-apps
```

页面按 OAuth client 汇总当前用户的活动 token，展示应用名称、scope、授权
时间、过期时间和活动会话数。撤销操作只会撤销当前用户授予该客户端的 token，
不会影响其他用户。

Gateway 不长期缓存授权结果。token 被标记为 `Revoked` 后，下一次
introspection 会返回无效，MCP 请求随即返回 401。

## 安全边界

- OAuth scope 只负责准入，不替代 Frappe DocType 权限。
- Personal 内部 API 必须使用断言中的用户上下文。
- 写操作必须经过参数校验并尽量支持幂等。
- 不允许 Gateway 传入任意 Python method、DocType 或 SQL。
- Nginx 必须使用 HTTPS，Gateway 端口只绑定本机或私有网络。
- 日志不得记录 access token、完整断言或 assertion secret。

## 配置 Gateway

Gateway 环境文件中的以下值必须与 Personal 一致：

```dotenv
FRAPPE_BASE_URL=http://personal:8000
FRAPPE_PUBLIC_URL=https://your-site.example
FRAPPE_SITE=your-site.example
MCP_PUBLIC_URL=https://your-site.example/mcp
MCP_ASSERTION_ISSUER=personal-mcp-sidecar
MCP_ASSERTION_AUDIENCE=personal-frappe-api
MCP_ASSERTION_HEADER=X-Personal-MCP-Assertion
MCP_REQUIRED_SCOPE=personal:mcp
```

完整 Gateway 配置见其仓库的
[配置文档](https://github.com/saoxia/frappe-mcp-gateway/blob/main/docs/configuration.md)。
