# Personal Docker deployment

The production stack lives at `/srv/pip` on the server and is managed with
Docker Compose:

```sh
cd /srv/pip
docker-compose build personal
docker-compose ps
docker-compose logs --tail=200
docker-compose up -d
docker-compose down
```

Persistent data:

- `/srv/pip/frappe-bench`: Bench, apps, sites, public/private files, logs, and
  the Python environment.
- `/srv/pip/frappe-ssh`: the `frappe` user's SSH keys.
- `/srv/pip/ssh-host-keys`: persistent SSH server host keys.
- `/srv/pip/redis/data`: Redis RDB/AOF data.
- `/srv/pip/nginx`: Nginx configuration, certificates, and logs.
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

Published ports:

- `80` and `443`: Nginx.
- `22222`: SSH inside the Personal container.
- `127.0.0.1:8000`: Frappe web, available only on the server.
- `127.0.0.1:9000`: Socket.IO, available only on the server.
- `127.0.0.1:6379`: Redis, available only on the server.
