#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/container_tools.log"
mkdir -p "${LOG_DIR}"

{
  echo "=== which yosys || true ==="
  which yosys || true
  echo

  echo "=== /opt/oss-cad-suite/bin/yosys -V || true ==="
  /opt/oss-cad-suite/bin/yosys -V || true
  echo

  echo "=== yosys -V || true ==="
  yosys -V || true
  echo

  echo "=== which openroad || true ==="
  which openroad || true
  echo

  echo "=== /usr/local/bin/openroad -version || true ==="
  /usr/local/bin/openroad -version || true
  echo

  echo "=== openroad -version || openroad -help || true ==="
  openroad -version || openroad -help || true
  echo

  echo "=== which klayout || true ==="
  which klayout || true
  echo

  echo "=== klayout -v || true ==="
  klayout -v || true
  echo

  echo "=== python3 --version ==="
  python3 --version
  echo

  echo "=== git --version ==="
  git --version
  echo

  echo "=== abc -h || yosys-abc -h || true ==="
  abc -h || yosys-abc -h || true
  echo

  if ! command -v openroad >/dev/null 2>&1; then
    echo "OpenROAD chưa có trong image. Có thể cần dùng official/prebuilt OpenROAD image hoặc build OpenROAD-flow-scripts."
  fi
} | tee "${LOG_FILE}"
