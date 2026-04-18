# GPU Setup Guide for DREAMPlace/Cypress

Hướng dẫn cài đặt nhanh trên GPU cloud mới (Vast.ai, RunPod, etc.)

## 1. System Dependencies

```bash
# Update và cài dependencies
apt-get update
apt-get install -y \
    git \
    cmake \
    build-essential \
    gcc-10 g++-10 \
    libboost-all-dev \
    bison \
    flex \
    libcairo2-dev \
    nvidia-cuda-toolkit \
    zlib1g-dev \
    libomp-dev \
    wget \
    unzip
```

## 2. Python & PyTorch

```bash
# PyTorch với CUDA support (đã test với CUDA 11.3)
pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 \
    --extra-index-url https://download.pytorch.org/whl/cu113

# NumPy < 2.0 (tương thích với code cũ)
pip install "numpy>=1.15.4,<2.0"

# Các dependencies khác
pip install scipy matplotlib cairocffi shapely \
    pyunpack patool pybind11
```

## 3. Clone & Build DREAMPlace

```bash
# Clone repository
git clone --recursive https://github.com/NVlabs/Cypress.git DREAMPlace
cd DREAMPlace

# Build với GCC-10 và CUDA support
mkdir build && cd build

CC=gcc-10 CXX=g++-10 cmake .. \
    -DCMAKE_INSTALL_PREFIX=../install \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -DCMAKE_CUDA_FLAGS="-gencode=arch=compute_86,code=sm_86" \
    -DCUB_DIR=../thirdparty/cub

# Build (30-60 phút tùy máy)
make -j$(nproc)

# Install
make install
```

## 4. Chạy Test

```bash
cd install

# Test với small benchmark
python3 dreamplace/Placer.py test/ispd2005/adaptec1.json
```

## 5. Troubleshooting

### Lỗi NumPy 2.0
```bash
pip install "numpy>=1.15.4,<2.0"
```

### Lỗi GCC version
```bash
# Luôn dùng GCC-10
export CC=gcc-10
export CXX=g++-10
```

### Lỗi CUDA not found
```bash
# Check CUDA
nvidia-smi
which nvcc

# Nếu thiếu: cài nvidia-cuda-toolkit
apt-get install nvidia-cuda-toolkit
```

### Lỗi CUB namespace (nếu có)
Thêm vào cmake:
```bash
-DCMAKE_CUDA_FLAGS="... -DCUB_NS_QUALIFIER=cub"
```

## 6. Quick Script (tự động hóa)

Lưu file `setup_gpu.sh`:

```bash
#!/bin/bash
set -e

echo "=== Installing system dependencies ==="
apt-get update
apt-get install -y git cmake build-essential gcc-10 g++-10 \
    libboost-all-dev bison flex libcairo2-dev nvidia-cuda-toolkit \
    zlib1g-dev libomp-dev wget unzip

echo "=== Installing Python packages ==="
pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 \
    --extra-index-url https://download.pytorch.org/whl/cu113
pip install "numpy>=1.15.4,<2.0"
pip install scipy matplotlib cairocffi shapely pyunpack patool

echo "=== Cloning DREAMPlace ==="
cd /home
git clone --recursive https://github.com/NVlabs/Cypress.git DREAMPlace
cd DREAMPlace

echo "=== Building DREAMPlace ==="
mkdir -p build && cd build
CC=gcc-10 CXX=g++-10 cmake .. \
    -DCMAKE_INSTALL_PREFIX=../install \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -DCMAKE_CUDA_FLAGS="-gencode=arch=compute_86,code=sm_86" \
    -DCUB_DIR=../thirdparty/cub

make -j$(nproc)
make install

echo "=== Setup complete ==="
echo "Test with: cd install && python3 dreamplace/Placer.py test/ispd2005/adaptec1.json"
```

Chạy script:
```bash
chmod +x setup_gpu.sh
./setup_gpu.sh
```

## 7. Lưu ý cho Vast.ai / RunPod

- **Image khởi đầu**: Chọn `pytorch/pytorch:1.11.0-cuda11.3-cudnn8-runtime`
- **Container Disk**: Tối thiểu 20GB (build cần nhiều space)
- **GPU**: RTX 3060/3090/4090 compute capability 8.6

## 8. Commit & Push lên GitHub

```bash
cd /home/DATN
git add GPU_SETUP_GUIDE.md
git commit -m "Add GPU setup guide for DREAMPlace"
git push origin main
```

Sau này khi thuê GPU mới, chỉ cần:
1. SSH vào container
2. Clone repo DATN
3. Chạy `./setup_gpu.sh`
4. Done!
