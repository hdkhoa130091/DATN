#!/bin/bash
# Setup script for DREAMPlace/Cypress on GPU cloud instances
# Run this on fresh GPU instances (Vast.ai, RunPod, etc.)

set -e

echo "=== GPU Setup for DREAMPlace/Cypress ==="
echo "Starting setup at $(date)"

# 1. System dependencies
echo "[1/6] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    git \
    cmake \
    build-essential \
    gcc-10 \
    g++-10 \
    libboost-all-dev \
    bison \
    flex \
    libcairo2-dev \
    nvidia-cuda-toolkit \
    zlib1g-dev \
    libomp-dev \
    wget \
    unzip \
    > /dev/null 2>&1

# 2. Python packages
echo "[2/6] Installing Python packages..."
pip install -q torch==1.11.0+cu113 torchvision==0.12.0+cu113 \
    --extra-index-url https://download.pytorch.org/whl/cu113
pip install -q "numpy>=1.15.4,<2.0"
pip install -q scipy matplotlib cairocffi shapely pyunpack patool pybind11

# 3. Clone DREAMPlace
echo "[3/6] Cloning DREAMPlace/Cypress..."
cd /home
if [ -d "DREAMPlace" ]; then
    echo "DREAMPlace already exists, skipping clone"
else
    git clone --recursive https://github.com/NVlabs/Cypress.git DREAMPlace
fi

# 4. Build
echo "[4/6] Building DREAMPlace (this may take 30-60 minutes)..."
cd DREAMPlace

# Clean old build if exists
rm -rf build install

mkdir -p build
cd build

CC=gcc-10 CXX=g++-10 cmake .. \
    -DCMAKE_INSTALL_PREFIX=../install \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -DCMAKE_CUDA_FLAGS="-gencode=arch=compute_86,code=sm_86" \
    -DCUB_DIR=../thirdparty/cub \
    > /dev/null 2>&1

make -j$(nproc) 2>&1 | tee build.log

# 5. Install
echo "[5/6] Installing..."
make install > /dev/null 2>&1

# 6. Verify
echo "[6/6] Verifying installation..."
cd ../install
python3 -c "import dreamplace; print('✓ DREAMPlace imported successfully')"

echo ""
echo "=== Setup Complete ==="
echo "Location: /home/DREAMPlace"
echo "Test command: cd /home/DREAMPlace/install && python3 dreamplace/Placer.py test/ispd2005/adaptec1.json"
echo "Finished at $(date)"
