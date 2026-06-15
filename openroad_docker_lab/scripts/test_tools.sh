#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/container_tools.log"
mkdir -p "${LOG_DIR}"

{
  echo "=== yosys -V ==="
  yosys -V
  echo

  echo "=== yosys-abc -h ==="
  yosys-abc -h | head -n 5 || true
  echo

  echo "=== abc -h ==="
  abc -h | head -n 5 || true
  echo

  echo "=== openroad -version ==="
  openroad -version
  echo

  echo "=== klayout -v ==="
  klayout -v || true
  echo

  echo "=== python3 --version ==="
  python3 --version
  echo

  echo "=== git --version ==="
  git --version
  echo
} | tee "${LOG_FILE}"
