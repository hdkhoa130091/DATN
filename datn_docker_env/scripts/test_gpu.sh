#!/usr/bin/env bash
set -e

mkdir -p logs

{
  echo "=== nvidia-smi || true ==="
  nvidia-smi || true
  echo

  python3 - << 'PY'
import torch
print("torch version:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("cuda version:", torch.version.cuda)
if torch.cuda.is_available():
    print("gpu count:", torch.cuda.device_count())
    print("gpu name:", torch.cuda.get_device_name(0))
else:
    print("Giải thích:")
    print("- Có thể đang cài PyTorch CPU-only.")
    print("- Container chưa chạy với --gpus all.")
    print("- Host thiếu NVIDIA Container Toolkit.")
    print("- Có thể có mismatch giữa driver và CUDA.")
PY
} 2>&1 | tee logs/gpu_check.log
