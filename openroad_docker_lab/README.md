# OpenROAD Docker Lab

## 1. Giới thiệu

`openroad_docker_lab` cung cấp một Docker image để gom toàn bộ môi trường
OpenROAD vào một container dùng chung cho:

- tổng hợp logic bằng Yosys và ABC từ `oss-cad-suite`
- chạy OpenROAD CLI
- chạy OpenROAD GUI khi thật sự cần quan sát layout
- chạy OpenROAD-flow-scripts (ORFS)
- chuẩn bị đầu ra phục vụ các bước tiếp theo như `flow.py` và RL

Mục tiêu của thư mục này là tạo ra một quy trình ổn định:

1. build image
2. vào container bằng CLI
3. kiểm tra tool bằng `test_tools.sh`
4. chạy synthesis, floorplan, placement bằng ORFS

## 2. Docker image này build những gì

Dockerfile hiện tại build đầy đủ các thành phần sau:

- base image `ubuntu:22.04`
- dependency hệ thống để build OpenROAD
- `oss-cad-suite` tại `/opt/oss-cad-suite`
- `yosys` và `yosys-abc` nằm trong `/opt/oss-cad-suite/bin`
- `bazelisk`
- OpenROAD build từ source, binary đặt tại:

```text
/usr/local/bin/openroad
```

- OpenROAD-flow-scripts clone vào:

```text
/opt/OpenROAD-flow-scripts
```

- `klayout`

Lưu ý quan trọng:

- `openroad` có sẵn trên `PATH`
- `yosys` có sẵn trong image nhưng nằm trong `oss-cad-suite`
- khi dùng `run_cli.sh`, `PATH` được bổ sung để gọi `yosys` trực tiếp
- nếu tự `docker run ... bash` mà không thêm `PATH`, lệnh `yosys` có thể không
  nhận dù binary vẫn tồn tại

## 3. Quy trình chuẩn trước khi chạy `test_tools.sh`

Đây là quy trình nên làm theo từ đầu đến cuối.

### Bước 1. Build image

Từ thư mục gốc repo:

```bash
cd /path/to/DATN
./openroad_docker_lab/scripts/build.sh
```

Kết quả mong đợi:

- Docker image `openroad-docker-lab:latest` được tạo thành công

### Bước 2. Vào container bằng CLI

```bash
./openroad_docker_lab/scripts/run_cli.sh
```

Đây là cách vào container nên dùng mặc định vì:

- ổn định hơn GUI
- ít lỗi hơn
- đã cấu hình `PATH` cho `yosys`
- mount repo vào:

```text
/workspace/DATN
```

### Bước 3. Chạy kiểm tra tool

Sau khi đã vào container:

```bash
cd /workspace/DATN/openroad_docker_lab
./scripts/test_tools.sh
```

Kết quả kiểm tra đúng là phải xác nhận được:

- OpenROAD chạy được
- Yosys chạy được
- `yosys-abc` hoặc ABC backend của Yosys có mặt
- KLayout chạy được
- Python và Git có mặt

Script sẽ ghi log tại:

```text
openroad_docker_lab/logs/container_tools.log
```

## 4. Cách hiểu kết quả `test_tools.sh`

Khi kiểm tra trong container, các trạng thái sau là bình thường:

- `which openroad` trả về `/usr/local/bin/openroad`
- `/usr/local/bin/openroad -version` chạy được
- `/opt/oss-cad-suite/bin/yosys -V` chạy được

Nếu bạn thấy:

```bash
yosys: command not found
```

thì có 2 khả năng:

- bạn không đi vào container bằng `run_cli.sh`
- hoặc `PATH` chưa chứa `/opt/oss-cad-suite/bin`

Điều này không có nghĩa là Yosys chưa được cài.

Tương tự, nếu `abc` không có trên `PATH` nhưng
`/opt/oss-cad-suite/bin/yosys-abc` chạy được thì backend ABC vẫn đã có sẵn.

## 5. Nên dùng `run_cli.sh` hay `run_gui_x11.sh`

Trong thực tế chỉ nên xem `run_cli.sh` là lối vào chính.

### `run_cli.sh`

Dùng cho hầu hết công việc:

- kiểm tra môi trường
- chạy `test_tools.sh`
- chạy Yosys
- chạy OpenROAD CLI
- chạy ORFS synthesis, floorplan, placement

Ưu điểm:

- ít lỗi nhất
- không phụ thuộc X11
- phù hợp cho server, SSH, máy thuê GPU và terminal từ xa

### `run_gui_x11.sh`

Chỉ dùng khi bạn thực sự muốn mở GUI để xem:

- DEF
- ODB
- floorplan
- placement
- routing

Không nên dùng script này làm bước khởi đầu để kiểm tra môi trường.

## 6. Cách mở OpenROAD GUI

Nếu host có X11 hoặc XWayland:

```bash
xhost +local:docker
./openroad_docker_lab/scripts/run_gui_x11.sh
```

Sau khi vào container GUI, chạy:

```bash
openroad -gui
```

Không cần thêm script kiểm tra GUI riêng.

## 7. Quy trình sử dụng khuyến nghị

Quy trình khuyến nghị cho người mới:

1. build image
2. vào bằng `run_cli.sh`
3. chạy `./scripts/test_tools.sh`
4. xác nhận Yosys, OpenROAD, KLayout, ORFS đã sẵn sàng
5. bắt đầu chạy synthesis hoặc ORFS
6. chỉ khi cần xem hình mới dùng `run_gui_x11.sh`

## 8. Quy trình synthesis

Tài liệu mô tả đầu vào, đầu ra, `config.mk`, `SDC`, các stage synthesis,
floorplan, placement và ví dụ Ariane133 nằm tại:

```text
openroad_docker_lab/SYNTHESIS_GUIDE.md
```

## 9. Lỗi thường gặp

### `docker: command not found`

Docker chưa được cài trên host hoặc shell hiện tại không có quyền gọi Docker.

### `yosys: command not found`

Thường là do `PATH`, không phải do image thiếu Yosys. Hãy vào container bằng:

```bash
./openroad_docker_lab/scripts/run_cli.sh
```

### `abc: command not found`

Trong image này, ABC thường được dùng dưới dạng `yosys-abc` từ
`oss-cad-suite`, không nhất thiết có binary tên `abc` trên `PATH`.

### `cannot connect to display`

Chỉ liên quan tới GUI. Nguyên nhân phổ biến:

- chưa chạy `xhost +local:docker`
- chưa truyền `DISPLAY`
- chưa mount `/tmp/.X11-unix`
- đang chạy qua SSH không có X11 forwarding

### `make DESIGN_CONFIG=...` lỗi

Có thể do:

- sai `config.mk`
- thiếu PDK hoặc enablement file
- version flow hoặc input design chưa đúng

## 10. Tóm tắt ngắn

Nếu chỉ muốn một quy trình chuẩn, hãy dùng đúng chuỗi lệnh này:

```bash
cd /path/to/DATN
./openroad_docker_lab/scripts/build.sh
./openroad_docker_lab/scripts/run_cli.sh
cd /workspace/DATN/openroad_docker_lab
./scripts/test_tools.sh
```

Nếu `test_tools.sh` xác nhận được `openroad`, `yosys`,
`/opt/oss-cad-suite/bin/yosys-abc`, `klayout`, `python3`, `git` thì môi trường
đã sẵn sàng cho synthesis và ORFS.
