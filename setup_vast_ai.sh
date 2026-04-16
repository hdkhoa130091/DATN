#!/bin/bash
# Setup script for DATN on Vast.ai with GPU support

set -e  # Exit on error

echo "=================================="
echo "DATN Setup Script for Vast.ai"
echo "=================================="

# 1. Check GPU
echo "[1/8] Checking GPU..."
nvidia-smi
if [ $? -ne 0 ]; then
    echo "ERROR: No GPU detected!"
    exit 1
fi

# 2. Install system dependencies
echo "[2/8] Installing system dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 python3-dev python3-pip python3-venv \
    build-essential cmake git wget curl \
    libboost-all-dev libeigen3-dev \
    zlib1g-dev libcairo2-dev \
    bison flex tcl swig \
    libssl-dev

# 3. Clone repository
echo "[3/8] Cloning DATN repository..."
cd ~
if [ ! -d "DATN" ]; then
    git clone --recursive https://github.com/hdkhoa130091/DATN.git
fi
cd DATN

# 4. Setup Python environment
echo "[4/8] Setting up Python environment..."
if [ ! -d "ct_env" ]; then
    python3 -m venv ct_env
fi
source ct_env/bin/activate

# 5. Install PyTorch with CUDA
echo "[5/8] Installing PyTorch with CUDA support..."
pip install --upgrade pip
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# 6. Install Python dependencies
echo "[6/8] Installing Python dependencies..."
pip install numpy pandas matplotlib cairocffi \
    tensorflow torch_optimizer ncg_optimizer timeout_decorator \
    absl-py tf-agents gym

# 7. Build DREAMPlace
echo "[7/8] Building DREAMPlace with GPU support..."
cd ~/DATN/DREAMPlace
mkdir -p build && cd build

cmake .. \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
    -DTORCH_ENABLE_CUDA=ON \
    -DCMAKE_BUILD_TYPE=Release

make -j$(nproc)
make install

# 8. Setup environment variables
echo "[8/8] Setting up environment variables..."
echo 'export PYTHONPATH="${HOME}/DATN/DREAMPlace:${HOME}/DATN/DREAMPlace/dreamplace:$PYTHONPATH"' >> ~/.bashrc
echo 'export PATH="${HOME}/DATN/ct_env/bin:$PATH"' >> ~/.bashrc
echo 'source ~/DATN/ct_env/bin/activate' >> ~/.bashrc

# Test installation
echo ""
echo "=================================="
echo "Testing installation..."
echo "=================================="

python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python3 -c "import dreamplace; print('DREAMPlace: OK')"

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. source ~/.bashrc"
echo "2. cd ~/DATN/circuit_training"
echo "3. Run training: python3 -m circuit_training.learning.train_ppo ..."
