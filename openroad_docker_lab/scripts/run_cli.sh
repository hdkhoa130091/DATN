#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"

echo "Chạy container CLI interactive..."
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -it \
  --name "${CONTAINER_NAME}" \
  -v "${ROOT_DIR}:/workspace" \
  -w /workspace \
  openroad-docker-lab:latest \
  bash
