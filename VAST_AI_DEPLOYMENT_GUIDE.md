# Vast.ai Deployment Guide for DATN

## 1. Chọn Template trên Vast.ai

**Recommended:**
- **OS:** Ubuntu 22.04 Desktop (hoặc 20.04)
- **GPU:** 2x RTX 3060 12GB (hoặc tương đương)
- **RAM:** Tối thiểu 32GB (khuyến nghị 64GB+ cho RL training)
- **Disk:** 100GB+ NVMe

## 2. Setup sau khi khởi động instance

### 2.1. Kiểm tra GPU
```bash
nvidia-smi
nvcc --version
```

### 2.2. Cài đặt dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 python3-dev python3-pip python3-venv \
    build-essential cmake git wget curl \
    libboost-all-dev libeigen3-dev \
    zlib1g-dev libcairo2-dev \
    bison flex tcl swig \
    libssl-dev
```

### 2.3. Clone DATN repository
```bash
cd ~
git clone --recursive https://github.com/hdkhoa130091/DATN.git
cd DATN
```

### 2.4. Setup Python Environment
```bash
# Tạo virtual environment
python3 -m venv ct_env
source ct_env/bin/activate

# Cài PyTorch với CUDA 11.8
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 \
    --index-url https://download.pytorch.org/whl/cu118

# Cài dependencies khác
pip install numpy pandas matplotlib cairocffi \
    tensorflow torch_optimizer ncg_optimizer timeout_decorator
```

### 2.5. Build DREAMPlace với GPU support
```bash
cd ~/DATN/DREAMPlace

# Tạo build directory
mkdir -p build && cd build

# Configure với GPU support
cmake .. \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
    -DTORCH_ENABLE_CUDA=ON \
    -DCMAKE_BUILD_TYPE=Release

# Build
make -j$(nproc)

# Install
make install
```

### 2.6. Setup environment variables
```bash
# Thêm vào ~/.bashrc
echo 'export PYTHONPATH="${HOME}/DATN/DREAMPlace:${HOME}/DATN/DREAMPlace/dreamplace:$PYTHONPATH"' >> ~/.bashrc
echo 'export PATH="${HOME}/ct_env/bin:$PATH"' >> ~/.bashrc

source ~/.bashrc
```

### 2.7. Test DREAMPlace GPU
```bash
cd ~/DATN/DREAMPlace/benchmarks/ispd2005/adaptec1
python3 -m dreamplace.Placer \
    --config ../config.json \
    --gpu 0  # Use GPU 0
```

### 2.8. Setup Circuit Training Environment
```bash
cd ~/DATN/circuit_training
pip install -e .

# Kiểm tra PLC wrapper
python3 -c "from circuit_training.environment import plc_client_os_wrapper; print('PLC wrapper OK')"
```

### 2.9. Chạy RL Training
```bash
cd ~/DATN/circuit_training

# Tạo output directory
mkdir -p ~/rl_output

# Chạy training
python3 -m circuit_training.learning.train_ppo \
    --root_dir=~/rl_output \
    --netlist_file=~/DATN/MacroPlacement/CodeElements/Plc_client/test/ariane_ng45/netlist.pb.txt \
    --init_placement=~/DATN/MacroPlacement/CodeElements/Plc_client/test/ariane_ng45/initial.plc \
    --replay_buffer_server_address=localhost:8000 \
    --variable_container_server_address=localhost:8001
```

## 3. Multi-GPU Training (tùy chọn)

Nếu muốn dùng cả 2 GPU:
```bash
export CUDA_VISIBLE_DEVICES=0,1

# Hoặc trong code, specify cả 2 GPU
python3 -m circuit_training.learning.train_ppo \
    --gpu_list=0,1 \
    ...
```

## 4. Lưu ý quan trọng

### 4.1. Vast.ai Instance Lifecycle
- **Save thường xuyên:** Vast.ai instances có thể bị dừng bất cứ lúc nào
- **Dùng Persistent Storage:** Lưu dữ liệu quan trọng ra ngoài instance
```bash
# Copy dữ liệu ra volume ngoài
cp -r ~/rl_output /mnt/persistent/
```

### 4.2. Tối ưu Performance
```bash
# Kiểm tra GPU utilization
watch -n 1 nvidia-smi

# Monitor training
tensorboard --logdir=~/rl_output
```

### 4.3. Troubleshooting

**Lỗi CUDA out of memory:**
```bash
# Giảm batch size hoặc dùng 1 GPU
export CUDA_VISIBLE_DEVICES=0
```

**Lỗi ImportError:**
```bash
# Kiểm tra PYTHONPATH
export PYTHONPATH="${HOME}/DATN/DREAMPlace:${HOME}/DATN/DREAMPlace/dreamplace:$PYTHONPATH"
```

**Lỗi ABI incompatibility:**
```bash
# Rebuild DREAMPlace với đúng PyTorch version
cd ~/DATN/DREAMPlace/build
make clean
cmake .. -DPYTHON_EXECUTABLE=$(which python3)
make -j$(nproc)
make install
```

## 5. Cost Estimate (Vast.ai)

| Config | Price/hr | 24h | 7 days |
|--------|----------|-----|--------|
| 2x RTX 3060 | ~$0.10 | $2.40 | $16.80 |
| 2x RTX 3090 | ~$0.30 | $7.20 | $50.40 |

**Khuyến nghị:** Dùng RTX 3060 12GB cho testing, chuyển sang RTX 3090/4090 cho training lớn.

## 6. Quick Commands

```bash
# Connect via SSH
ssh root@<instance_ip> -p <port>

# Copy files từ local
scp -P <port> -r local_folder root@<instance_ip>:~/

# Sync về local
scp -P <port> -r root@<instance_ip>:~/rl_output ./
```
