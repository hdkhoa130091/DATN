# DATN RL Docker Environment

## 1. Docker này dùng để làm gì

`datn_docker_env` là Docker environment dành cho phần RL và Python workflow của
repo DATN.

Mục tiêu chính:

- chạy code Python trong `rl_macroplacement_agent`
- train hoặc evaluate agent RL
- kiểm tra môi trường `torch`, `yosys`, source `DREAMPlace`
- mount trực tiếp repo DATN từ máy host vào container để không phải rebuild khi
  chỉ sửa code Python

## 2. Image này hiện chứa những gì

Image được build với tên:

```text
datn-openroad-rl:latest
```

Dockerfile hiện tại cài các thành phần sau:

- `python3`, `pip`, `venv`
- tool build cơ bản: `cmake`, `ninja`, `gcc/g++`, `make`, `swig`, `bison`,
  `flex`
- thư viện Python cơ bản: `numpy`, `scipy`, `pandas`, `matplotlib`,
  `networkx`, `tqdm`, `pyyaml`, `tensorboard`, `gymnasium`
- `torch`, `torchvision`, `torchaudio`
- `stable-baselines3`
- `yosys`
- clone source `DREAMPlace` vào:

```text
/opt/DREAMPlace
```

Image này hỗ trợ tốt cho:

- chạy script Python/RL
- kiểm tra mount dữ liệu testcase
- kiểm tra Yosys
- kiểm tra source DREAMPlace

Image này **chưa phải** môi trường GPU hoàn chỉnh cho PyTorch CUDA, vì
Dockerfile hiện tại đang cài:

```text
https://download.pytorch.org/whl/cpu
```

Vì vậy:

- container GPU vẫn chạy được với `--gpus all`
- nhưng `torch.cuda.is_available()` có thể vẫn là `False`

## 3. Vì sao cần `.env`

Repo DATN không được copy cứng vào image. Thay vào đó, repo trên máy host sẽ
được mount vào container tại:

```text
/workspace/DATN
```

Do đó cần file `.env` để chỉ ra đường dẫn repo DATN trên host.

### Tạo `.env`

```bash
cd /path/to/DATN/datn_docker_env
cp .env.example .env
```

### Nội dung quan trọng trong `.env`

Biến bắt buộc và thực sự được dùng bởi các script hiện tại là:

```text
DATN_PATH=/duong/dan/toi/repo/DATN
```

Ví dụ:

```text
DATN_PATH=/home/khoahd/Documents/DATN-1
```

Hai dòng còn lại trong `.env.example`:

```text
IMAGE_NAME=datn-openroad-rl:latest
CONTAINER_NAME=datn_openroad_rl
```

hiện chưa được các script `run_cpu.sh` và `run_gpu.sh` sử dụng trực tiếp.

## 4. Quy trình build và chạy

### Bước 1. Build image

```bash
cd /path/to/DATN
./datn_docker_env/scripts/build.sh
```

Build log được lưu tại:

```text
datn_docker_env/logs/build.log
```

### Bước 3. Chạy container GPU

```bash
./datn_docker_env/scripts/run_gpu.sh
```

Container tạm thời này chạy với tên:

```text
datn_openroad_rl_gpu
```

Điều kiện để chạy bản GPU:

- host có NVIDIA driver
- host có NVIDIA Container Toolkit
- Docker hỗ trợ `--gpus all`
### Option: Chạy container CPU-based
Nếu không hỗ trợ card đồ họa GPU cho ứng dụng học tăng cường thì có thể chạy bằng CPU

Ưu điểm: 
- Tiện lợi cho tất cả các loại mấy tính

Nhược điểm: 
- "Ngốn" RAM, trong khi RAM nên được dùng để mở và chạy OpenROAD đối với nghiên cứu này
            
- Chậm hơn nhiều, performance thấp hơn nhiều so với 
```bash
./datn_docker_env/scripts/run_cpu.sh
```

Container tạm thời này chạy với tên:

```text
datn_openroad_rl_cpu
```
## 5. Docker này hỗ trợ những workflow nào

### Workflow phù hợp

- train RL bằng Python
- evaluate policy/model
- chạy các script trong `rl_macroplacement_agent/scripts`
- kiểm tra feature extraction, rollout logic, PPO code
- kiểm tra mount dữ liệu trong repo DATN
- chạy test Yosys đơn giản

### Workflow không nên kỳ vọng từ Docker này

- full OpenROAD flow
- ORFS hoàn chỉnh
- GUI OpenROAD
- PyTorch CUDA chắc chắn hoạt động ngay từ lần build đầu

## 6. Test Docker thì cần thỏa mãn những gì

Một lần test hợp lệ cho Docker RL nên xác nhận được 4 nhóm điều kiện:

### 1. Python environment hoạt động

Container cần chạy được:

- `python3`
- `pip`
- import `torch`

### 2. Repo DATN được mount đúng

Trong container phải nhìn thấy:

- `MacroPlacement/`
- `rl_macroplacement_agent/`
- `tools/`

và các file testcase như `.plc`, `.sdc`, `.lef`, `.lib` phải tìm được từ
`/workspace/DATN`.

### 3. Yosys hoạt động

Container phải chạy được một test Yosys nhỏ, ví dụ synth adder đơn giản và ghi
ra `netlist.v`.

### 4. DREAMPlace source tồn tại

Container phải nhìn thấy source ở:

```text
/opt/DREAMPlace
```

Lưu ý: nhìn thấy source **không có nghĩa** DREAMPlace đã build xong.

### 5. GPU test chỉ pass khi nào

Nếu bạn chạy container GPU, test GPU chỉ được xem là pass hoàn toàn khi:

- `nvidia-smi` chạy được trong container
- `torch.cuda.is_available()` trả về `True`

Nếu `nvidia-smi` có nhưng `torch.cuda.is_available()` vẫn là `False` thì
container mới chỉ pass phần mount GPU ở mức Docker, chưa pass phần PyTorch CUDA.

## 7. Các script test và ý nghĩa

Sau khi vào container:

```bash
cd /workspace/DATN/datn_docker_env
```

### Test tổng quát container

```bash
./scripts/test_container.sh
```

Xác nhận:

- Python
- pip
- git
- cmake
- ninja
- yosys
- biến `DREAMPLACE_HOME`
- mount `/workspace/DATN`

### Test mount repo DATN

```bash
./scripts/test_datn_mount.sh
```

Xác nhận:

- repo mount đúng
- nhìn thấy các thư mục quan trọng
- tìm được input như `netlist.pb.txt`, `.plc`, `.sdc`, `.lef`, `.lib`

### Test Yosys

```bash
./scripts/test_yosys.sh
```

Xác nhận:

- Yosys chạy được
- pass `abc`
- ghi được `netlist.v`

### Test DREAMPlace

```bash
./scripts/test_dreamplace.sh
```

Xác nhận:

- source `DREAMPlace` đã được clone
- `torch` import được

### Test GPU

```bash
./scripts/test_gpu.sh
```

Xác nhận:

- `nvidia-smi`
- `torch.cuda.is_available()`
- số lượng GPU và tên GPU nếu CUDA thực sự hoạt động

## 8. Quy trình test khuyến nghị

### Kiểm tra trên host trước

```bash
cd /path/to/DATN/datn_docker_env
./scripts/test_host.sh
```

### Kiểm tra trong container CPU

```bash
./scripts/run_cpu.sh
cd /workspace/DATN/datn_docker_env
./scripts/test_container.sh
./scripts/test_datn_mount.sh
./scripts/test_yosys.sh
./scripts/test_dreamplace.sh
```

### Kiểm tra trong container GPU

```bash
./scripts/run_gpu.sh
cd /workspace/DATN/datn_docker_env
./scripts/test_container.sh
./scripts/test_gpu.sh
./scripts/test_dreamplace.sh
```

## 9. Kết luận ngắn

Docker này nên được hiểu là:

- một Python/RL container cho DATN
- có Yosys
- có source DREAMPlace
- mount repo DATN để chạy code thật

Nó chưa nên được xem là:

- full OpenROAD container
- guaranteed CUDA training container

Nếu mục tiêu tiếp theo của bạn là train RL bằng GPU thật trong Docker, bước hợp
lý tiếp theo là sửa `Dockerfile` sang base CUDA và cài PyTorch CUDA tương ứng.
