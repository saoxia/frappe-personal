# Server deployment notes

Sensitive values are stored locally in `.env.server.local`. That file is ignored
by Git and must never be committed.

## Topology

- Public domain: `pip.lly.info`
- The domain also has a hosts-file mapping on the server.
- The production stack is managed from `/srv/pip/docker-compose.yml`.
- Frappe runs in the Docker container named `personal` on the
  `personal-network` bridge.
- The Personal runtime image is built from `/srv/pip/personal/Dockerfile` and
  tagged `personal:runtime`.
- Nginx runs in the independent Docker container named `nginx`.
- Redis runs in the independent Docker container named `redis`.
- Bench root: `/home/frappe/frappe-bench`
- Frappe site: `pip.lly.info`
- Integration-test site: `pip-test.localhost`
- MariaDB runs in the Docker container named `db`.
- Site database: `pip`
- Site database host: `10.8.0.16:3306`
- MariaDB allows the production site user from Docker gateway `172.17.0.1`.
- MariaDB administrative user: `root`
- The MariaDB password is stored only in `.env.server.local`.
- Node binaries: `/home/frappe/.nvm/versions/node/v24.13.0/bin`

## Ports and persistence

- Nginx publishes `80` and `443`.
- Personal publishes SSH on `22222`.
- Frappe Web and Socket.IO are mapped only on the server loopback interface as
  `127.0.0.1:8000` and `127.0.0.1:9000`.
- Redis is mapped only on the server loopback interface as
  `127.0.0.1:6379`.
- Bench, apps, sites, uploaded files, logs, and the Python environment persist
  at `/srv/pip/frappe-bench`.
- The `frappe` user's SSH keys persist at `/srv/pip/frappe-ssh`.
- SSH server host keys persist at `/srv/pip/ssh-host-keys`.
- Redis RDB/AOF data persists at `/srv/pip/redis/data`.
- Nginx configuration, certificates, and logs persist below
  `/srv/pip/nginx`.
- Optional Personal SSH passwords are stored only in `/srv/pip/.env`.
- Current deployment configuration checksums are recorded in
  `/srv/pip/backups/current-deployment.sha256`.

## Operating conventions

Run Frappe and Bench commands inside the `personal` container. Always identify
the site directory first and pass the site explicitly to Bench commands:

```sh
docker exec personal sh -lc 'cd /home/frappe/frappe-bench && ls apps/ sites/ Procfile'
docker exec personal sh -lc 'cd /home/frappe/frappe-bench && bench --site pip.lly.info list-apps'
```

Manage the split stack with:

```sh
cd /srv/pip
docker-compose build personal
docker-compose ps
docker-compose logs --tail=200
docker-compose up -d
docker-compose restart
```

Before destructive database or App operations, verify the selected site,
installed App name, MariaDB container, and database name.

Run automated tests only on `pip-test.localhost`, never on the production site.

The image supplies Node and Bench paths through both the container environment
and `/etc/profile.d/frappe.sh`. Asset builds can therefore run directly:

```sh
docker exec personal sh -lc 'cd /home/frappe/frappe-bench && bench build --app personal'
```
