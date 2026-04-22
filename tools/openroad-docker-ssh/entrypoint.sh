#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${CONTAINER_USER:-openroad}"
USER_HOME="/home/${USER_NAME}"
AUTH_KEYS_FILE="${USER_HOME}/.ssh/authorized_keys"

mkdir -p "${USER_HOME}/.ssh"
touch "${AUTH_KEYS_FILE}"

if [[ -n "${AUTHORIZED_KEY:-}" ]]; then
  printf '%s\n' "${AUTHORIZED_KEY}" >"${AUTH_KEYS_FILE}"
fi

chown -R "${USER_NAME}:${USER_NAME}" "${USER_HOME}/.ssh"
chmod 700 "${USER_HOME}/.ssh"
chmod 600 "${AUTH_KEYS_FILE}"

exec /usr/sbin/sshd -D -e
