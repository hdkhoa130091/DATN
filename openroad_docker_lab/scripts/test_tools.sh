#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/container_tools.log"
mkdir -p "${LOG_DIR}"

{
  echo "=== make --version ==="
  make --version | head -n 1
  echo

  echo "=== yosys -V ==="
  yosys -V
  echo

  echo "=== yosys-abc -h ==="
  yosys-abc -h | head -n 5 || true
  echo

  echo "=== abc check ==="
  if command -v abc >/dev/null 2>&1; then
    abc -h | head -n 5 || true
  else
    echo "abc not found on PATH"
  fi
  echo

  echo "=== openroad -version ==="
  openroad -version
  echo

  echo "=== tclsh patchlevel ==="
  tclsh <<< 'puts [info patchlevel]'
  echo

  echo "=== klayout -b -v ==="
  klayout -b -v || true
  echo

  echo "=== xauth -V ==="
  xauth -V || true
  echo

  echo "=== DISPLAY check ==="
  if [ -n "${DISPLAY:-}" ]; then
    echo "DISPLAY=${DISPLAY}"
  else
    echo "DISPLAY is not set"
  fi
  echo

  echo "=== python3 --version ==="
  python3 --version
  echo

  echo "=== git --version ==="
  git --version
  echo
} | tee "${LOG_FILE}"
