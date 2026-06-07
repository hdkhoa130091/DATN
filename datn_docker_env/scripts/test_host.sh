#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/host_check.log"
mkdir -p "${LOG_DIR}"

{
  echo "=== docker --version ==="
  docker --version
  echo

  echo "=== docker compose version || docker-compose --version || true ==="
  docker compose version || docker-compose --version || true
  echo

  echo "=== uname -a ==="
  uname -a
  echo

  echo "=== id ==="
  id
  echo

  echo "=== groups ==="
  groups
  echo

  echo "=== DISPLAY ==="
  echo "${DISPLAY:-}"
  echo

  echo "=== WAYLAND_DISPLAY ==="
  echo "${WAYLAND_DISPLAY:-}"
  echo

  echo "=== nvidia-smi || true ==="
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi || true
  else
    echo "nvidia-smi không có trên host. Điều này chỉ có nghĩa là host chưa có CLI NVIDIA trong PATH hoặc không dùng GPU NVIDIA."
  fi
} 2>&1 | tee "${LOG_FILE}"

if command -v timeout >/dev/null 2>&1; then
  DOCKER_PS_OUTPUT="$(timeout 8s docker ps 2>&1 || true)"
  DOCKER_PS_STATUS="$?"
else
  DOCKER_PS_OUTPUT="$(docker ps 2>&1 || true)"
  DOCKER_PS_STATUS="$?"
fi

if [[ "${DOCKER_PS_STATUS}" == "124" ]]; then
  echo "docker ps bị treo quá lâu. Có thể Docker daemon đang kẹt hoặc môi trường hiện tại không phản hồi đúng."
  echo "Chi tiết hiện có: không thu được output hữu ích từ docker ps trong thời gian chờ."
elif echo "${DOCKER_PS_OUTPUT}" | grep -qiE "permission denied|cannot connect|is the docker daemon running|error during connect"; then
  cat <<'EOF'
Docker hiện chưa chạy được với user hiện tại.
Hãy kiểm tra:
1. Docker daemon đã chạy chưa.
2. User đã nằm trong group docker chưa.
3. Nếu vừa thêm vào group docker, hãy đăng xuất/đăng nhập lại.
EOF
  echo
  echo "Chi tiết lỗi docker ps:"
  echo "${DOCKER_PS_OUTPUT}"
else
  echo "Docker có vẻ đang dùng được với user hiện tại."
fi
