# OpenROAD Docker Lab

## 1. Docker image này dùng để làm gì

Project này tạo một Docker image/container để thử nghiệm:

- OpenROAD CLI
- Yosys
- OpenROAD-flow-scripts
- một số dependency cơ bản cho flow EDA
- kiểm tra khả năng chạy GUI bằng X11/XWayland

Mục tiêu chính là có một môi trường tách biệt với host, dễ thử nghiệm và dễ dọn dẹp.

## 2. Vì sao OpenROAD CLI dễ hơn GUI

OpenROAD CLI dễ chạy hơn vì:

- không phụ thuộc vào display server
- không cần truyền `DISPLAY`
- không cần mount socket X11
- ít lỗi hơn khi chạy qua Docker

Vì vậy nên ưu tiên kiểm tra `openroad` ở chế độ CLI trước, sau đó mới thử GUI.

## 3. Muốn dùng GUI trong Docker cần gì

Để dùng OpenROAD GUI trong Docker, bạn thường cần:

- X11 hoặc XWayland đang hoạt động trên host
- biến môi trường `DISPLAY`
- mount `/tmp/.X11-unix`
- đôi khi cần `xhost +local:docker`

Nếu chạy từ xa, thường nên dùng:

- `ssh -Y`
- hoặc VNC/noVNC

## 4. Cách build image

```bash
./scripts/build.sh
```

Image sẽ được build với tên:

```text
openroad-docker-lab:latest
```

## 5. Cách chạy CLI

```bash
./scripts/run_cli.sh
```

Container sẽ mount thư mục project vào:

```text
/workspace
```

và mở `bash` để bạn tự thao tác.

## 6. Cách chạy GUI

Trên host:

```bash
xhost +local:docker
./scripts/run_gui_x11.sh
```

Sau khi vào container, bạn có thể chạy:

```bash
./scripts/test_gui.sh
```

hoặc:

```bash
openroad -gui
```

## 7. Cách kiểm tra tools

Trong container, chạy:

```bash
./scripts/test_tools.sh
```

Script sẽ ghi log vào:

```text
logs/container_tools.log
```

## 8. Cách chạy OpenROAD-flow-scripts gcd nếu có

Trong container, chạy:

```bash
./scripts/run_orfs_gcd.sh
```

Script sẽ:

- kiểm tra `/opt/OpenROAD-flow-scripts` hoặc `./OpenROAD-flow-scripts`
- tìm config `gcd`
- thử chạy `make DESIGN_CONFIG=...`
- không tự tải PDK nếu chưa có sẵn
- ghi log vào `logs/orfs_gcd.log`

## 9. Giải thích lỗi thường gặp

### `openroad command not found`

Điều này nghĩa là OpenROAD chưa có trong image. Có thể cần:

- dùng prebuilt OpenROAD package đúng version
- dùng official/prebuilt OpenROAD image
- hoặc build OpenROAD từ source

### `cannot connect to display`

Các nguyên nhân phổ biến:

- chưa chạy `xhost +local:docker` trên host
- `DISPLAY` chưa được truyền vào container
- `/tmp/.X11-unix` chưa được mount
- host đang dùng Wayland nhưng XWayland chưa hoạt động
- đang chạy remote và cần `ssh -Y` hoặc VNC/noVNC

### thiếu `.lef`, `.lib`, `.sdc`

Đây là lỗi phổ biến khi chạy flow EDA. OpenROAD-flow-scripts cần đủ enablement và input file.

### thiếu PDK

ORFS không thể chạy đầy đủ nếu thiếu PDK, LEF, Liberty và các dữ liệu công nghệ liên quan.

### `make DESIGN_CONFIG` lỗi

Có thể do:

- config không tồn tại
- thiếu dependency
- thiếu PDK
- version OpenROAD không tương thích với ORFS

## 10. Ghi chú quan trọng về OpenROAD GUI

OpenROAD GUI có thể mở ODB/DEF để xem:

- layout
- floorplan
- placement
- routing

Nếu chạy từ xa, cần X11 forwarding hoặc VNC/noVNC.

## 11. Ghi chú về OpenROAD trong image này

Project này hiện **ưu tiên build OpenROAD mới từ source** để giảm lệch version
với `OpenROAD-flow-scripts`.

Dockerfile hiện:

- dùng `ubuntu:22.04`
- cài dependency cơ bản
- cài `oss-cad-suite` để có `yosys` mới hơn
- cài `bazelisk`
- clone và build `OpenROAD` từ source vào `/opt/OpenROAD-install`
- clone `OpenROAD-flow-scripts` vào `/opt/OpenROAD-flow-scripts`

Điều này làm thời gian build image lâu hơn, nhưng đổi lại binary `openroad` mới
hơn và ít phải vá tương thích thủ công khi chạy ORFS.
