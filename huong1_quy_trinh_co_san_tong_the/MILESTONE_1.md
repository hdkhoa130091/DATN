# Dựng Nền EDA Và Tạo Artifact Ban Đầu

## Mục tiêu

Tài liệu này tập trung vào việc dựng được nền tảng EDA open-source đủ ổn định để phục vụ các bước sau của toàn bộ quy trình.

Ở giai đoạn này, trọng tâm chưa nằm ở parser hay RL, mà nằm ở:

- dựng được flow EDA open-source thay cho Genus/Innovus
- chạy được một baseline physical design có thể lặp lại
- sinh ra các artifact đủ tốt để làm đầu vào cho giai đoạn tiếp theo
- có cách quan sát checkpoint bằng GUI khi cần

Mục tiêu cốt lõi là:

- hình thành một môi trường EDA có thể sử dụng lâu dài cho nghiên cứu
- xác nhận rằng quy trình physical design bằng công cụ mã nguồn mở là khả thi và tái lập được
- tạo ra bộ dữ liệu implementation đầu tiên để làm đầu vào cho các bước chuyển đổi dữ liệu và RL về sau

## Vị trí Trong Toàn Bộ Quy Trình

Giai đoạn này đóng vai trò:

- tạo nền dữ liệu EDA thật
- chứng minh OpenROAD/ORFS chạy được
- tạo ra artifact thực để sau đó dùng tiếp các translator, `plc_client`, và flow RL có sẵn

Nói ngắn gọn:

- nếu giai đoạn này chưa xong thì toàn bộ quy trình chưa có đầu vào EDA đáng tin cậy

Đây là giai đoạn nền tảng:

- nó không giải quyết trực tiếp bài toán học tăng cường
- nhưng nó quyết định toàn bộ chất lượng và độ tin cậy của dữ liệu đầu vào cho các bước phía sau

## Bảng tổng hợp

| Hạng mục | Nội dung |
|---|---|
| Mục tiêu | Dựng baseline EDA open-source và sinh ra artifact vật lý ổn định |
| Công việc | Cài toolchain, tải ORFS, cài OpenROAD, cài Yosys mới, patch tương thích, chạy sample flow, cấu hình VNC |
| Đầu vào | Ubuntu 22.04, repo nghiên cứu, `OpenROAD-flow-scripts`, OpenROAD binary, `OSS CAD Suite` |
| Đầu ra | `1_synth.*`, `2_floorplan.*`, `3_place.*`, và ưu tiên đạt `6_final.*` |
| Tiêu chí hoàn thành | Sinh ra được artifact mục tiêu và flow có thể chạy lặp lại |

## Nhóm đầu vào và vai trò của từng thành phần

Ở giai đoạn này, đầu vào nên được nhìn như các nhóm hạ tầng kỹ thuật cần thiết cho flow EDA.

### 1. Hạ tầng hệ thống

- `Ubuntu 22.04`:
  - Là hệ điều hành nền cho môi trường nghiên cứu.
  - Công dụng: cung cấp môi trường ổn định để cài đặt và vận hành flow EDA.
- các gói hệ thống:
  - Là nhóm thư viện và công cụ phụ trợ của hệ điều hành.
  - Công dụng: hỗ trợ biên dịch, Tcl, Python, GUI từ xa và các nhu cầu hạ tầng của flow.

### 2. Công cụ điều phối và thực thi flow

- `OpenROAD-flow-scripts`:
  - Là bộ script điều phối luồng thiết kế số tự động.
  - Công dụng: tổ chức và gọi các bước của flow như synthesis, floorplan, placement, CTS, routing và báo cáo.
- `OpenROAD`:
  - Là công cụ physical design mã nguồn mở cho thiết kế vi mạch số.
  - Công dụng: thực hiện các bước thiết kế vật lý như floorplan, placement, CTS, routing và trích xuất báo cáo.
- `Yosys`:
  - Là công cụ tổng hợp logic mã nguồn mở.
  - Công dụng: chuyển RTL/Verilog thành netlist logic để làm đầu vào cho các bước physical design.

### 3. Công cụ tương thích và hỗ trợ

- `OSS CAD Suite`:
  - Là bộ công cụ EDA đóng gói sẵn.
  - Công dụng: cung cấp phiên bản `Yosys` và các công cụ liên quan khi gói hệ thống chưa đáp ứng.
- script patch tương thích:
  - Là tập lệnh hiệu chỉnh khác biệt giữa các phiên bản công cụ.
  - Công dụng: giúp ORFS và OpenROAD phối hợp ổn định trong môi trường thực tế.
- `TigerVNC`:
  - Là công cụ desktop từ xa.
  - Công dụng: hỗ trợ quan sát checkpoint và dùng GUI mượt hơn so với X11 forwarding.

## Phần mềm và công cụ cần có

- Ubuntu 22.04
- `OpenROAD`
- `OpenROAD-flow-scripts`
- `OSS CAD Suite`
- `KLayout`
- `TigerVNC`
- Python 3.10+

Các gói hệ thống nên cài:

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y \
  curl wget git make cmake ninja-build pkg-config \
  flex bison swig tcl-dev python3 python3-pip python3-venv \
  iverilog verilator klayout magic netgen gtkwave \
  tigervnc-standalone-server tigervnc-common xfce4 xfce4-terminal
```

Ghi chú vận hành thực tế:

- `python3`, `cmake`, `make`, `openroad`, `klayout` cần có sẵn trong hệ thống.
- `yosys` không nhất thiết phải có trong `PATH` hệ thống nếu đã dùng bản trong `OSS CAD Suite`.
- nếu tải lại `OpenROAD-flow-scripts`, cần chạy lại script patch tương thích trước khi chạy flow.

## Mục tiêu

1. Dựng đủ toolchain cần thiết.
2. Đồng bộ các phiên bản công cụ ở mức chạy được thực tế.
3. Chạy một sample flow có thể lặp lại.
4. Chốt bộ artifact vật lý đầu tiên.

## Quy trình thực hiện

### Bước 1: Dựng workspace

```bash
cd /home
git clone https://github.com/hdkhoa130091/DATN.git
cd /home/DATN
```

### Bước 2: Tải OpenROAD-flow-scripts

```bash
cd /home/DATN
curl -L https://codeload.github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/tar.gz/refs/heads/master \
  -o orfs.tar.gz
tar -xzf orfs.tar.gz
mv OpenROAD-flow-scripts-master OpenROAD-flow-scripts
rm -f orfs.tar.gz
```

### Bước 3: Cài OpenROAD

```bash
cd /tmp
curl -L \
  https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb \
  -o openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y ./openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
```

### Bước 4: Cài OSS CAD Suite để lấy Yosys mới

```bash
cd /home/DATN
curl -L \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-21/oss-cad-suite-linux-x64-20260421.tgz \
  -o oss-cad-suite-linux-x64-20260421.tgz
mkdir -p /home/DATN/oss-cad-suite-20260421
tar -xzf oss-cad-suite-linux-x64-20260421.tgz \
  -C /home/DATN/oss-cad-suite-20260421 --strip-components=1
```

### Bước 5: Patch tương thích ORFS

Workspace hiện có sẵn:

- [tools/patch_orfs_compat.py](/home/DATN/tools/patch_orfs_compat.py)

Chạy:

```bash
python3 /home/DATN/tools/patch_orfs_compat.py
```

Sau khi patch, có thể kiểm tra nhanh:

```bash
sed -n '143,155p' /home/DATN/OpenROAD-flow-scripts/flow/scripts/floorplan.tcl
```

Nếu patch đúng, dòng sửa timing ở `floorplan.tcl` phải ở dạng:

```tcl
repair_timing_helper -setup -skip_last_gasp
```

Lưu ý:

- nếu bạn vừa xóa và tải lại `OpenROAD-flow-scripts`, phải chạy lại bước patch này.
- nếu không patch, flow có thể dừng ở `floorplan` với lỗi `repair_timing -sequence is not a known keyword or flag`.

### Bước 6: Chạy baseline flow

Khi chạy trên máy mới hoặc khi thư mục kết quả đang trống, nên chạy toàn bộ flow từ đầu:

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  -j1
```

Nếu đã có checkpoint route và chỉ muốn chạy phần cuối, mới dùng:

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  do-finish -j1
```

Điều kiện để dùng `do-finish`:

- đã có `results/nangate45/gcd/base/5_route.odb`
- đã có `results/nangate45/gcd/base/5_route.sdc`

Nếu chưa có các file trên, `do-finish` sẽ dừng ở `6_1_fill` với lỗi thiếu `5_route.odb`.

Khi cần làm sạch kết quả dở dang trước khi chạy lại:

```bash
rm -rf /home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base
rm -rf /home/DATN/OpenROAD-flow-scripts/flow/logs/nangate45/gcd/base
rm -rf /home/DATN/OpenROAD-flow-scripts/flow/reports/nangate45/gcd/base
rm -rf /home/DATN/OpenROAD-flow-scripts/flow/objects/nangate45/gcd/base
```

Lý do dùng `-j1`:

- log dễ theo dõi hơn
- tránh che mất lỗi tương thích khi đang dựng môi trường lần đầu
- phù hợp để kiểm chứng milestone nền tảng

## Đầu vào của giai đoạn

- máy Ubuntu
- OpenROAD
- ORFS
- Yosys từ OSS CAD Suite
- sample design `nangate45/gcd`

## Đầu ra mong muốn

Tối thiểu:

- `1_synth.odb`
- `2_floorplan.odb`
- `3_place.odb`

Ưu tiên đạt:

- `6_final.odb`
- `6_final.def`
- `6_final.sdc`
- `6_final.v`
- `6_final.spef`

Đường dẫn hiện tại:

- `/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base`

Ý nghĩa của các đầu ra này:

- `1_synth.*`:
  - Là đầu ra của giai đoạn tổng hợp logic.
  - Công dụng: xác nhận netlist logic đã được tạo thành công.
- `2_floorplan.*`:
  - Là đầu ra của giai đoạn floorplan.
  - Công dụng: cung cấp thông tin hình học, boundary và bố cục cơ sở của thiết kế.
- `3_place.*`:
  - Là đầu ra của giai đoạn placement.
  - Công dụng: xác nhận các phần tử đã được đặt vị trí trong mặt bằng chip.
- `6_final.*`:
  - Là bộ đầu ra implementation gần hoàn chỉnh.
  - Công dụng: làm nguồn dữ liệu EDA chính để chuyển sang các bước tiếp theo.

## Trạng thái kiểm chứng

Đã kiểm chứng thực tế trên môi trường này:

- ORFS mới tải về cần patch tương thích trước khi chạy.
- sau khi patch, flow đi qua được `synth`, `floorplan`, `place`, `cts`, `route`, `fill` và tạo được `6_final.*`.
- `yosys` đang được gọi từ `/home/DATN/oss-cad-suite-20260421/bin/yosys`, không phải từ `PATH` hệ thống.
- flow hiện dừng ở `final_report` do lỗi GUI `invalid command name "get_scenes"` trong `save_images.tcl`.

Các artifact cuối đã sinh ra trước khi dừng:

- `6_final.odb`
- `6_final.def`
- `6_final.sdc`
- `6_final.v`
- `6_final.spef`

Điểm cần nhớ khi vận hành:

- thiếu thư mục `OpenROAD-flow-scripts` thì phải tải lại trước khi chạy.
- tải lại ORFS xong phải patch lại ngay.
- thư mục kết quả trống thì chạy `make ... -j1` từ đầu, không chạy `do-finish`.
- nếu dừng ở `final_report` với lỗi `get_scenes`, vẫn có thể xem đây là đã đạt mục tiêu artifact chính của giai đoạn nền tảng.

## GUI và quan sát checkpoint

Khi cần xem checkpoint bằng GUI, nên dùng helper VNC:

- [tools/openroad-remote-gui/README.md](/home/DATN/tools/openroad-remote-gui/README.md)

Ở giai đoạn này, GUI chỉ đóng vai trò:

- xem `2_floorplan.odb`
- xem `3_place.odb`
- xem `6_final.odb`

Không nên dùng GUI làm cách chạy chính cho flow dài.
