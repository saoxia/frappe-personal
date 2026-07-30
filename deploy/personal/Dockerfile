# syntax=docker/dockerfile:1.7

# Runtime dependencies and version defaults follow frappe/frappe_docker:
# https://github.com/frappe/frappe_docker/tree/f137f05d799a6a00d203b4c0d316a8f475e51778/images
ARG PYTHON_VERSION=3.14.2
ARG DEBIAN_BASE=bookworm

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE}

ARG NODE_VERSION=24.13.0
ARG NVM_VERSION=0.39.5
ARG FRAPPE_BENCH_VERSION=5.31.0
ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG WKHTMLTOPDF_DISTRO=bookworm
ARG WKHTMLTOPDF_AMD64_SHA256=98ba0d157b50d36f23bd0dedf4c0aa28c7b0c50fcdcdc54aa5b6bbba81a3941d
ARG INSTALL_CHROMIUM=true
ARG DEBIAN_FRONTEND=noninteractive

ENV HOME=/home/frappe \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    NVM_DIR=/home/frappe/.nvm \
    PATH=/home/frappe/.local/bin:/home/frappe/.nvm/versions/node/v${NODE_VERSION}/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin \
    BENCH_DEVELOPER=1 \
    PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

LABEL org.opencontainers.image.source="https://github.com/frappe/frappe_docker" \
    org.opencontainers.image.description="Personal Frappe Bench runtime with SSH; Nginx and Redis run separately"

RUN groupadd --gid 1000 frappe \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends --yes \
        bash-completion \
        build-essential \
        curl \
        file \
        gettext-base \
        git \
        gpg \
        jq \
        libbz2-dev \
        libffi-dev \
        libharfbuzz0b \
        liblcms2-dev \
        libldap2-dev \
        liblzma-dev \
        libmariadb-dev \
        libncurses-dev \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libpangoft2-1.0-0 \
        libpq-dev \
        libreadline-dev \
        libsasl2-dev \
        libsqlite3-dev \
        libtiff-dev \
        libwebp-dev \
        locales \
        mariadb-client \
        media-types \
        openssh-server \
        passwd \
        pkg-config \
        postgresql-client \
        redis-tools \
        restic \
        sudo \
        tk8.6-dev \
        vim \
        xz-utils \
        zlib1g-dev \
    && if [[ "${INSTALL_CHROMIUM}" == "true" ]]; then \
        apt-get install --no-install-recommends --yes chromium-headless-shell; \
    fi \
    && sed -i 's/^# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && printf '%s\n' 'frappe ALL=(ALL:ALL) ALL' > /etc/sudoers.d/frappe \
    && chmod 0440 /etc/sudoers.d/frappe \
    && rm -rf /var/lib/apt/lists/*

RUN case "$(dpkg --print-architecture)" in \
        amd64) wkhtml_arch=amd64 ;; \
        *) echo "Only amd64 is supported by this pinned deployment image" >&2; exit 1 ;; \
    esac \
    && package="wkhtmltox_${WKHTMLTOPDF_VERSION}.${WKHTMLTOPDF_DISTRO}_${wkhtml_arch}.deb" \
    && curl --fail --silent --show-error --location --output "/tmp/${package}" \
        "https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTMLTOPDF_VERSION}/${package}" \
    && echo "${WKHTMLTOPDF_AMD64_SHA256}  /tmp/${package}" | sha256sum --check --status \
    && apt-get update \
    && apt-get install --no-install-recommends --yes "/tmp/${package}" \
    && rm -f "/tmp/${package}" \
    && rm -rf /var/lib/apt/lists/*

USER frappe
WORKDIR /home/frappe

RUN curl --fail --silent --show-error --location \
        "https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh" \
        | bash \
    && source "${NVM_DIR}/nvm.sh" \
    && nvm install "${NODE_VERSION}" \
    && nvm use "v${NODE_VERSION}" \
    && nvm alias default "${NODE_VERSION}" \
    && npm install --global yarn \
    && corepack enable pnpm \
    && rm -rf "${NVM_DIR}/.cache" \
    && printf '%s\n' \
        'export NVM_DIR="/home/frappe/.nvm"' \
        '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' \
        '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' \
        'export PATH="/home/frappe/.local/bin:$PATH"' \
        'export BENCH_DEVELOPER=1' \
        >> /home/frappe/.bashrc

RUN python -m pip install --no-cache-dir --user \
    "frappe-bench==${FRAPPE_BENCH_VERSION}"

USER root

COPY sshd_config /etc/ssh/sshd_config.d/personal.conf
COPY profile.sh /etc/profile.d/frappe.sh
COPY entrypoint.sh /usr/local/bin/personal-entrypoint

RUN install -d -m 0755 /etc/ssh/host-keys /run/sshd \
    && chmod 0644 /etc/profile.d/frappe.sh \
    && chmod 0755 /usr/local/bin/personal-entrypoint

WORKDIR /home/frappe/frappe-bench

EXPOSE 22222 6787 8000 9000

STOPSIGNAL SIGTERM

ENTRYPOINT ["/usr/local/bin/personal-entrypoint"]
CMD ["bench", "start"]
