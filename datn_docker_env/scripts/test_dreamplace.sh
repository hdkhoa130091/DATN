#!/usr/bin/env bash
set -e

mkdir -p logs

{
  echo "=== DREAMPLACE_HOME ==="
  echo "${DREAMPLACE_HOME:-}"
  echo

  echo "=== ls -la \$DREAMPLACE_HOME || true ==="
  ls -la "${DREAMPLACE_HOME}" || true
  echo

  echo "=== find \$DREAMPLACE_HOME -maxdepth 3 -type f | head -50 || true ==="
  find "${DREAMPLACE_HOME}" -maxdepth 3 -type f | head -50 || true
  echo

  python3 - << 'PY'
import sys
print(sys.version)
try:
    import torch
    print("torch ok", torch.__version__)
except Exception as e:
    print("torch import error:", e)
PY

  echo
  echo "DREAMPlace source có thể đã clone nhưng chưa build. Cần build đúng CUDA/PyTorch/GCC/CMake."
} 2>&1 | tee logs/dreamplace_test.log
