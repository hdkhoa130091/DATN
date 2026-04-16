# RL for Chip Design - Circuit Training

Dự án triển khai học tăng cường (Reinforcement Learning) cho thiết kế vi mạch.

## Cấu trúc thư mục

```
DATN/
├── circuit_training/          # RL Engine (Google Research)
│   ├── circuit_training/      # Source code
│   └── ...
├── MacroPlacement/            # Benchmarks (TILOS Institute)
│   ├── Testcases/             # Ariane, Mempool, etc.
│   └── Flows/                 # OpenROAD flows
├── DREAMPlace/                # GPU Placement Engine
│   ├── src/                   # C++/CUDA source
│   └── ...
├── dreamplace/                # Stub module (đã cài đặt)
│   └── __init__.py
├── setup.py                   # Setup dreamplace stub
├── checkgpu.py                # Kiểm tra GPU
├── quick_test_training.py     # Test script
└── COMPLETE_DEPLOYMENT_GUIDE.md  # Hướng dẫn chi tiết
```

## Quick Start

### 1. Kiểm tra môi trường
```bash
py checkgpu.py
py quick_test_training.py
```

### 2. Test import Circuit Training
```bash
py -c "import sys; sys.path.insert(0, 'circuit_training'); from circuit_training.environment.environment import CircuitEnv; print('SUCCESS')"
```

### 3. Xem hướng dẫn chi tiết
- Mở file `COMPLETE_DEPLOYMENT_GUIDE.md`
- Đọc từng bước triển khai
- Chạy training theo hướng dẫn

## Yêu cầu đã cài đặt

✅ Python 3.10
✅ TensorFlow 2.15.0
✅ PyTorch 2.5.1 (CUDA 11.8)
✅ TF-Agents 0.19.0
✅ Circuit Training repo
✅ MacroPlacement repo
✅ DREAMPlace repo

## Next Steps

1. Đọc `COMPLETE_DEPLOYMENT_GUIDE.md`
2. Chạy `quick_test_training.py` để kiểm tra
3. Bắt đầu training với PPO

## Tài liệu tham khảo

- Paper: "A graph placement methodology for fast chip design" (Nature 2021)
- Blog: https://deepmind.google/discover/blog/how-alphachip-transformed-computer-chip-design/
- Circuit Training: https://github.com/google-research/circuit_training
- MacroPlacement: https://github.com/TILOS-AI-Institute/MacroPlacement
