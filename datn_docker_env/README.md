# DATN Docker Environment

## 1. Kiến trúc mong muốn

### Host

- chứa repo `DATN`
- dùng VSCode để code
- dùng Git để quản lý source

### Docker image

- chứa OpenROAD
- chứa Yosys
- chứa DREAMPlace
- chứa PyTorch
- chứa các dependency phục vụ synthesis, placement, RL và evaluation

### Container

- chạy synthesis
- chạy placement
- chạy DREAMPlace
- chạy RL training
- chạy evaluation
- output và log được lưu ra repo DATN trên host

## 2. Vì sao không copy DATN vào image

Không copy cứng repo DATN vào image trong giai đoạn phát triển vì:

- sửa code nhanh hơn
- không phải rebuild image mỗi lần sửa source
- output và log nằm trên host nên dễ theo dõi
- dễ `git commit` ngay trên repo thật

Repo DATN sẽ được mount từ host vào container tại:

```text
/workspace/DATN
```

## 3. Cách setup

```bash
cp .env.example .env
```

Sau đó sửa:

```text
DATN_PATH=/duong/dan/toi/repo/DATN
```

Rồi build:

```bash
./scripts/build.sh
```

## 4. Cách chạy CPU

```bash
./scripts/run_cpu.sh
```

## 5. Cách chạy GPU

```bash
./scripts/run_gpu.sh
```

Lưu ý:

- host cần có NVIDIA driver
- host cần có NVIDIA Container Toolkit
- container cần chạy với `--gpus all`

## 6. Cách chạy GUI

Trên host:

```bash
xhost +local:docker
./scripts/run_gui_x11.sh
```

Trong container:

```bash
xeyes
openroad -gui
```

## 7. Cách test

### Trên host

```bash
./scripts/test_host.sh
```

### Sau khi vào container

```bash
./scripts/test_container.sh
./scripts/test_gpu.sh
./scripts/test_yosys.sh
./scripts/test_openroad.sh
./scripts/test_dreamplace.sh
./scripts/test_datn_mount.sh
```

## 8. Giải thích Docker

- `image` là môi trường đóng gói sẵn
- `container` là một phiên chạy cụ thể từ image

Trong project này:

- image chứa tool và dependency
- container mount repo DATN từ host để chạy code thật

## 9. Ghi chú về OpenROAD

Dockerfile hiện ưu tiên:

1. thử cài `openroad` từ apt nếu có
2. nếu không có thì clone `OpenROAD-flow-scripts` vào `/opt/OpenROAD-flow-scripts`
3. không tự build OpenROAD từ source ở bước này

Biến môi trường:

```text
ORFS_HOME=/opt/OpenROAD-flow-scripts
```

Nếu `openroad` chưa có trong image, bạn sẽ thấy thông báo rõ trong:

```bash
./scripts/test_openroad.sh
```

## 10. Ghi chú về DREAMPlace

Dockerfile hiện:

- clone source DREAMPlace vào `/opt/DREAMPlace`
- không tự build vì còn phụ thuộc tương thích CUDA, PyTorch, GCC, CMake

Biến môi trường:

```text
DREAMPLACE_HOME=/opt/DREAMPlace
```

Nếu DREAMPlace chưa build, script test sẽ báo rõ:

```text
DREAMPlace source có thể đã clone nhưng chưa build. Cần build đúng CUDA/PyTorch/GCC/CMake.
```

## 11. Giải thích lỗi thường gặp

### Docker không chạy được

Hãy kiểm tra:

- Docker daemon đã chạy chưa
- user đã nằm trong group `docker` chưa
- nếu vừa thêm vào group `docker`, cần đăng xuất/đăng nhập lại

### `openroad command not found`

Điều này nghĩa là image chưa có binary OpenROAD sẵn. Khi đó cần:

- dùng prebuilt image phù hợp
- cài package nếu có
- hoặc build OpenROAD / ORFS ở bước sau

### `torch.cuda.is_available() == False`

Các nguyên nhân phổ biến:

- đang cài PyTorch CPU-only
- container chưa chạy với `--gpus all`
- host thiếu NVIDIA Container Toolkit
- driver và CUDA không tương thích

### `cannot connect to display`

Các nguyên nhân phổ biến:

- chưa chạy `xhost +local:docker`
- chưa truyền `DISPLAY`
- chưa mount `/tmp/.X11-unix`
- host đang dùng Wayland nhưng XWayland chưa hoạt động

