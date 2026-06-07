#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

if [[ -z "${DATN_PATH:-}" ]]; then
  echo "Biến DATN_PATH chưa được thiết lập. Hãy tạo .env từ .env.example." >&2
  exit 1
fi

if [[ ! -d "${DATN_PATH}" ]]; then
  echo "Đường dẫn DATN_PATH không tồn tại: ${DATN_PATH}" >&2
  exit 1
fi

echo "Lưu ý: host cần có NVIDIA driver và NVIDIA Container Toolkit để --gpus all hoạt động đúng."

docker run -it --rm \
  --gpus all \
  --shm-size=16g \
  --name datn_openroad_rl_gpu \
  -v "${DATN_PATH}:/workspace/DATN" \
  -w /workspace/DATN \
  datn-openroad-rl:latest bash
