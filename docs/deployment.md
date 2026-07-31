# 部署与运维

## 部署组成

生产 Compose 定义位于 `deploy/docker-compose.yml`，包含：

- `personal`：Frappe Web、Socket.IO、scheduler 和 worker 所在的 Bench
  运行环境；
- `redis`：独立 Redis 7；
- `nginx`：独立 TLS 反向代理；
- `mcp`：从 `/srv/frappe-mcp-gateway` 构建的独立 MCP Gateway。

MariaDB 作为独立数据库服务存在，不由该 Compose 文件创建。

## 首次准备

目标目录示例：

```text
/srv/pip/
├── docker-compose.yml
├── personal/
├── nginx/
├── frappe-bench/
├── redis/data/
├── frappe-ssh/
├── ssh-host-keys/
├── .env
└── mcp.env

/srv/frappe-mcp-gateway/
```

先克隆两个仓库：

```sh
git clone https://github.com/saoxia/frappe-personal.git /srv/personal-source
git clone https://github.com/saoxia/frappe-mcp-gateway.git \
  /srv/frappe-mcp-gateway
```

将 `deploy/` 内容放到实际 stack 目录，并根据域名、证书和持久化路径调整配置。
不要把真实密码、OAuth secret、数据库密码或 assertion secret 提交到仓库。

## 配置密钥

`/srv/pip/.env` 可保存可选 SSH 密码：

```dotenv
PERSONAL_SSH_FRAPPE_PASSWORD=
PERSONAL_SSH_ROOT_PASSWORD=
```

`/srv/pip/mcp.env` 保存 Gateway 配置及至少 32 字符的 assertion secret，权限
应为 `0600`：

```sh
chmod 600 /srv/pip/.env /srv/pip/mcp.env
```

同一个 assertion secret 必须配置到 Frappe 站点的
`mcp_assertion_secret`。

## 构建与启动

```sh
cd /srv/pip
docker compose config --quiet
docker compose build personal mcp
docker compose up -d
docker compose ps
```

所有服务都应进入 `healthy` 状态。

## 更新 Personal

先更新持久化 Bench 中的 App，再迁移、构建资源并根据需要重建镜像：

```sh
docker exec -u 1000:1000 personal bash -lc '
  cd /home/frappe/frappe-bench/apps/personal &&
  git pull --ff-only origin main
'

docker exec -u 1000:1000 personal bash -lc '
  cd /home/frappe/frappe-bench &&
  bench --site your-site.example migrate &&
  bench build --app personal
'

cd /srv/pip
docker compose up -d --force-recreate personal
```

所有 Bench 命令都必须明确指定站点。更新前先备份数据库和站点文件。

## 更新 MCP Gateway

```sh
cd /srv/frappe-mcp-gateway
git pull --ff-only origin main

cd /srv/pip
docker compose build mcp
docker compose up -d --no-deps --force-recreate mcp
```

## Nginx

修改配置后先检查，再平滑 reload：

```sh
docker exec nginx nginx -t
docker exec nginx nginx -s reload
```

生产环境只应公开 `80`、`443` 和按需开放的 SSH 端口。Frappe Web、
Socket.IO、Redis 和 MCP 映射到 `127.0.0.1`。

## 验证

```sh
curl -fsS https://your-site.example/api/method/ping
curl -fsS \
  https://your-site.example/.well-known/oauth-protected-resource/mcp

curl -i \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  -d '{}' \
  https://your-site.example/mcp
```

未授权 MCP 请求应返回 `401` 和 `WWW-Authenticate: Bearer`。还应使用测试
用户验证 OAuth 登录、工具调用和 `/authorized-apps` 撤销流程。

## 日志

```sh
cd /srv/pip
docker compose logs --tail=200 personal
docker compose logs --tail=200 mcp
docker compose logs --tail=200 nginx
docker compose logs --tail=200 redis
```

日志不得包含密码、OAuth access token、完整内部断言或 assertion secret。

## 备份

至少备份：

- MariaDB 站点数据库；
- `sites/<site>/public/files`；
- `sites/<site>/private/files`；
- site config 与 common site config；
- Nginx 证书和配置；
- 恢复所需的密钥及其安全副本。

Redis AOF 不能代替 MariaDB 和站点文件备份。

## 清理原则

只有在新容器健康、外部入口验证通过并确认备份可用后，才能删除旧容器、旧
镜像或候选构建目录。删除容器前先核对 bind mount，避免误删宿主机持久化
数据。
