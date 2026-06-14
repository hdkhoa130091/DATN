#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "${LAB_DIR}/.." && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "Khong tim thay image ${IMAGE_NAME}. Chay ./scripts/build.sh truoc."
  exit 1
fi

if ! docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
  echo "Tao container ${CONTAINER_NAME}..."
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}:/workspace/DATN" \
    -w /workspace/DATN \
    "${IMAGE_NAME}" \
    sleep infinity >/dev/null
elif [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}")" != "true" ]; then
  echo "Khoi dong container ${CONTAINER_NAME}..."
  docker start "${CONTAINER_NAME}" >/dev/null
fi

echo "Vao container ${CONTAINER_NAME}. Project nam tai /workspace/DATN"
docker exec -it \
  -e PATH="/opt/oss-cad-suite/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  -w /workspace/DATN \
  "${CONTAINER_NAME}" \
  bash
