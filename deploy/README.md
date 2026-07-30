# Personal Docker deployment

The production stack lives at `/srv/pip` on the server and is managed with
Docker Compose:

```sh
cd /srv/pip
docker compose build personal mcp
docker compose up -d
docker compose ps
docker compose logs --tail=200
docker compose down
```

Persistent data:

- `/srv/pip/frappe-bench`: Bench, apps, sites, public/private files, logs, and
  the Python environment.
- `/srv/pip/frappe-ssh`: the `frappe` user's SSH keys.
- `/srv/pip/ssh-host-keys`: persistent SSH server host keys.
- `/srv/pip/redis/data`: Redis RDB/AOF data.
- `/srv/pip/nginx`: Nginx configuration, certificates, and logs.
- `/srv/pip/mcp.env`: root-readable MCP sidecar settings and assertion secret.
- `/srv/frappe-mcp-gateway`: independent checkout of the MCP gateway.
- `/srv/pip/backups/current-deployment.sha256`: current deployment
  configuration checksums.

The Personal image is built from `personal/Dockerfile`. Its dependency versions and
non-root `frappe` user layout are based on the official
[`frappe/frappe_docker`](https://github.com/frappe/frappe_docker) images at
commit `f137f05d799a6a00d203b4c0d316a8f475e51778`. This deployment intentionally
keeps an existing, bind-mounted Bench running under `bench start`; Nginx and
Redis are separate services, while the official production topology also
splits the backend, WebSocket, workers, and scheduler into individual
containers.

The image contains the Frappe runtime and build toolchain but no application or
site data. Bench, apps, sites, assets, logs, and the Python environment are
supplied by the `/srv/pip/frappe-bench` bind mount. Ansible and `screen` are not
installed because they are not used at runtime. Chromium is included, matching
the current official image default. Optional SSH passwords are read from
`/srv/pip/.env`:

```dotenv
PERSONAL_SSH_FRAPPE_PASSWORD=
PERSONAL_SSH_ROOT_PASSWORD=
```

Clone the independent gateway repository before building the stack:

```sh
git clone https://github.com/saoxia/frappe-mcp-gateway.git \
  /srv/frappe-mcp-gateway
```

Create `/srv/pip/mcp.env` from the gateway repository's `.env.example`, replace
`MCP_ASSERTION_SECRET` with a random value of at least 32 characters, and set
its mode to `0600`. The same secret must be stored as
`mcp_assertion_secret` in the Frappe site configuration.

The standalone gateway source is maintained at
[`saoxia/frappe-mcp-gateway`](https://github.com/saoxia/frappe-mcp-gateway).
Its endpoint is `https://pip.lly.info/mcp`. It validates the client's Frappe
OAuth token on every request and requires the `openid` and `personal:mcp`
scopes. It calls Frappe with a one-time, 60-second internal assertion instead
of forwarding the OAuth token. Users can revoke OAuth access at
`https://pip.lly.info/authorized-apps`; a revoked token is rejected on the next
MCP request.

Published ports:

- `80` and `443`: Nginx.
- `22222`: SSH inside the Personal container.
- `127.0.0.1:8000`: Frappe web, available only on the server.
- `127.0.0.1:9000`: Socket.IO, available only on the server.
- `127.0.0.1:6379`: Redis, available only on the server.
- `127.0.0.1:8100`: MCP sidecar, available only on the server; Nginx exposes
  `/mcp`.
