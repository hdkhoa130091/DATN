#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-openroad-ssh:jammy}"
CONTAINER_NAME="${CONTAINER_NAME:-openroad-ssh}"
SSH_KEY_PATH="${SSH_KEY_PATH:-${SCRIPT_DIR}/id_ed25519}"
SSH_PORT="${SSH_PORT:-2222}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed. Install docker.io first."
  exit 1
fi

if [[ ! -f "${SSH_KEY_PATH}" ]]; then
  ssh-keygen -t ed25519 -N "" -f "${SSH_KEY_PATH}" >/dev/null
fi

AUTHORIZED_KEY="$(cat "${SSH_KEY_PATH}.pub")"

docker build -t "${IMAGE_NAME}" "${SCRIPT_DIR}"

if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${SSH_PORT}:22" \
  -e AUTHORIZED_KEY="${AUTHORIZED_KEY}" \
  -e CONTAINER_USER="openroad" \
  -v "${REPO_ROOT}:/workspace" \
  -w /workspace \
  "${IMAGE_NAME}" >/dev/null

echo "Container ${CONTAINER_NAME} is running."
echo "SSH key: ${SSH_KEY_PATH}"
echo "Connect with:"
echo "  ssh -X -i ${SSH_KEY_PATH} -p ${SSH_PORT} -o StrictHostKeyChecking=no openroad@127.0.0.1"
