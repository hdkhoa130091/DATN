#!/usr/bin/env bash
set -e

mkdir -p logs

{
  echo "=== python3 --version ==="
  python3 --version
  echo

  echo "=== pip --version ==="
  pip --version
  echo

  echo "=== git --version ==="
  git --version
  echo

  echo "=== cmake --version ==="
  cmake --version
  echo

  echo "=== ninja --version || true ==="
  ninja --version || true
  echo

  echo "=== yosys -V || true ==="
  yosys -V || true
  echo

  echo "=== openroad -version || openroad -help || true ==="
  openroad -version || openroad -help || true
  echo

  echo "=== klayout -v || true ==="
  klayout -v || true
  echo

  echo "=== ORFS_HOME ==="
  echo "${ORFS_HOME:-}"
  echo

  echo "=== DREAMPLACE_HOME ==="
  echo "${DREAMPLACE_HOME:-}"
  echo

  echo "=== ls -la /workspace/DATN || true ==="
  ls -la /workspace/DATN || true
} 2>&1 | tee logs/container_check.log
