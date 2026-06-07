#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

if [[ -z "${DATN_PATH:-}" || ! -d "${DATN_PATH}" ]]; then
  echo "DATN_PATH chưa đúng hoặc không tồn tại." >&2
  exit 1
fi

if [[ -z "${DISPLAY:-}" ]]; then
  echo "Không có DISPLAY. GUI X11/XWayland không chạy được trong phiên hiện tại." >&2
  exit 1
fi

echo "Trên host hãy chạy trước:"
echo "xhost +local:docker"
echo

ARGS=(
  -it --rm
  --name datn_openroad_rl_gui
  --gpus all
  -e "DISPLAY=${DISPLAY}"
  -v /tmp/.X11-unix:/tmp/.X11-unix
  -v "${DATN_PATH}:/workspace/DATN"
  -w /workspace/DATN
)

if [[ -n "${XAUTHORITY:-}" && -f "${XAUTHORITY}" ]]; then
  ARGS+=(-v "${XAUTHORITY}:/root/.Xauthority:ro")
fi

docker run "${ARGS[@]}" datn-openroad-rl:latest bash
