#!/usr/bin/env bash
set -e

mkdir -p logs

{
  echo "=== pwd ==="
  pwd
  echo

  echo "=== ls -la ==="
  ls -la
  echo

  echo "=== git status || true ==="
  git status || true
  echo

  echo "=== find . -maxdepth 2 -type f | head -50 ==="
  find . -maxdepth 2 -type f | head -50
  echo

  echo "=== circuit_training ==="
  ls -la circuit_training || true
  echo

  echo "=== MacroPlacement ==="
  ls -la MacroPlacement || true
  echo

  echo "=== rl_macroplacement_agent ==="
  ls -la rl_macroplacement_agent || true
  echo

  echo "=== tools ==="
  ls -la tools || true
  echo

  echo "=== find inputs ==="
  find . -name "netlist.pb.txt" | head -20
  find . -name "*.plc" | head -20
  find . -name "*.sdc" | head -20
  find . -name "*.lib" | head -20
  find . -name "*.lef" | head -20
} 2>&1 | tee logs/datn_mount_test.log
