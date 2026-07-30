# Server deployment notes

Sensitive values are stored locally in `.env.server.local`. That file is ignored
by Git and must never be committed.

## Topology

- Public domain: `pip.lly.info`
- The domain also has a hosts-file mapping on the server.
- Frappe runs in the Docker container named `pip`.
- Bench root: `/home/frappe/frappe-bench`
- Frappe site: `pip.lly.info`
- Integration-test site: `pip-test.localhost`
- The `pip` container uses host networking.
- Nginx runs inside the `pip` container.
- MariaDB runs in the Docker container named `db`.
- Site database: `pip`
- Site database host: `10.8.0.16:3306`
- MariaDB administrative user: `root`
- The MariaDB password is stored only in `.env.server.local`.
- Node binaries: `/home/frappe/.nvm/versions/node/v24.13.0/bin`
- Pending GitHub deploy key: `/home/frappe/.ssh/frappe_personal_deploy`

## Operating conventions

Run Frappe and Bench commands inside the `pip` container. Always identify the
site directory first and pass the site explicitly to Bench commands:

```sh
docker exec pip sh -lc 'cd /home/frappe/frappe-bench && ls apps/ sites/ Procfile'
docker exec pip sh -lc 'cd /home/frappe/frappe-bench && bench --site pip.lly.info list-apps'
```

Before destructive database or App operations, verify the selected site,
installed App name, MariaDB container, and database name.

Run automated tests only on `pip-test.localhost`, never on the production site.

The non-interactive container shell does not include Node in `PATH`. For asset
builds, prepend the recorded Node directory:

```sh
docker exec pip sh -lc 'export PATH=/home/frappe/.nvm/versions/node/v24.13.0/bin:$PATH; cd /home/frappe/frappe-bench && bench build --app personal'
```
