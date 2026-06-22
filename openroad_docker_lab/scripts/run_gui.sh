#!/usr/bin/env bash
set -e

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "${LAB_DIR}/.." && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_gui}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"

if [[ -z "${DISPLAY:-}" ]]; then
  echo "Không có DISPLAY, X11 GUI không chạy được. Hãy dùng VNC/noVNC hoặc chạy trên desktop session có XWayland."
  exit 1
fi

echo "Trước khi chạy GUI, hãy cho phép Docker truy cập X11 trên host:"
echo "  xhost +local:docker"
echo

ARGS=(
  -it
  --name "${CONTAINER_NAME}"
  --net=host
  -e "DISPLAY=${DISPLAY}"
  -v /tmp/.X11-unix:/tmp/.X11-unix
  -v "${PROJECT_DIR}:/workspace/DATN"
  -w /workspace/DATN
)

# Dùng --net=host để đơn giản hóa việc giao tiếp với X11/XWayland trên Linux host.
if [[ -n "${XAUTHORITY:-}" && -f "${XAUTHORITY}" ]]; then
  ARGS+=(-v "${XAUTHORITY}:/root/.Xauthority:ro")
fi

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run "${ARGS[@]}" "${IMAGE_NAME}" bash
