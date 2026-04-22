#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY_PATH="${SSH_KEY_PATH:-${SCRIPT_DIR}/id_ed25519}"
SSH_PORT="${SSH_PORT:-2222}"

exec ssh -X \
  -i "${SSH_KEY_PATH}" \
  -p "${SSH_PORT}" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  openroad@127.0.0.1
