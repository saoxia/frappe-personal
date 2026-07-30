#!/bin/bash
set -euo pipefail

set_password() {
	local user=$1
	local password=$2

	if [[ -n "${password}" ]]; then
		printf '%s:%s\n' "${user}" "${password}" | chpasswd
	fi
}

set_password frappe "${FRAPPE_SSH_PASSWORD:-}"
set_password root "${ROOT_SSH_PASSWORD:-}"

mkdir -p /run/sshd
/usr/sbin/sshd -t
/usr/sbin/sshd

exec runuser --user frappe --preserve-environment -- "$@"
