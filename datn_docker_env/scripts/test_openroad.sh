#!/usr/bin/env bash
set -e

mkdir -p logs

{
  echo "=== which openroad || true ==="
  which openroad || true
  echo

  echo "=== openroad -version || openroad -help || true ==="
  openroad -version || openroad -help || true
  echo

  if ! command -v openroad >/dev/null 2>&1; then
    echo "OpenROAD chưa có trong image. Cần dùng prebuilt image, cài package, hoặc build OpenROAD/OpenROAD-flow-scripts."
  else
    echo "=== openroad -exit ==="
    openroad -exit
  fi
} 2>&1 | tee logs/openroad_test.log
