# Milestone 1 - Dựng Nền EDA Open-Source

## Mục tiêu

Milestone 1 có nhiệm vụ dựng nền EDA open-source đủ ổn định để phục vụ các bước sau của đồ án.

Mục tiêu của milestone này không phải là RL, mà là:

- thay thế flow thương mại bằng công cụ open-source
- chạy được physical design baseline có thể lặp lại
- sinh artifact vật lý thật để dùng cho các bước chuẩn hóa dữ liệu và đánh giá placement

## Kết luận kỹ thuật cần nhớ

Milestone 1 chứng minh rằng:

- `OpenROAD` và `OpenROAD-flow-scripts` có thể đóng vai trò backend vật lý thay cho flow thương mại
- `Yosys` có thể thay phần synthesis cơ bản
- có thể tạo artifact implementation thật để làm đầu vào cho pipeline nghiên cứu macro placement

Milestone này không nhằm chạy AlphaChip.

## Công cụ sử dụng

- Ubuntu 22.04
- `OpenROAD`
- `OpenROAD-flow-scripts`
- `Yosys` từ `OSS CAD Suite`
- `KLayout`
- `TigerVNC`
- Python 3.10+

## Đầu vào

- repo DATN
- `OpenROAD-flow-scripts`
- OpenROAD binary
- `OSS CAD Suite`
- sample design `nangate45/gcd`

## Đầu ra mong muốn

- `1_synth.*`
- `2_floorplan.*`
- `3_place.*`
- `6_final.odb`
- `6_final.def`
- `6_final.sdc`
- `6_final.v`
- `6_final.spef`

## Ý nghĩa đối với toàn bộ dự án

Milestone 1 tạo nền cho các bước sau:

- có backend vật lý open-source để kiểm chứng placement
- có workflow EDA thật thay cho giả lập
- có cơ sở để quay placement từ RL trở lại flow vật lý ở milestone 4

## Quy trình thực hiện

### 1. Clone repo

```bash
cd /home
git clone https://github.com/hdkhoa130091/DATN.git
cd /home/DATN
```

### 2. Tải ORFS

```bash
cd /home/DATN
curl -L https://codeload.github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/tar.gz/refs/heads/master \
  -o orfs.tar.gz
tar -xzf orfs.tar.gz
mv OpenROAD-flow-scripts-master OpenROAD-flow-scripts
rm -f orfs.tar.gz
```

### 3. Cài OpenROAD

```bash
cd /tmp
curl -L \
  https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb \
  -o openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y ./openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
```

### 4. Cài OSS CAD Suite để lấy Yosys

```bash
cd /home/DATN
curl -L \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-21/oss-cad-suite-linux-x64-20260421.tgz \
  -o oss-cad-suite-linux-x64-20260421.tgz
mkdir -p /home/DATN/oss-cad-suite-20260421
tar -xzf oss-cad-suite-linux-x64-20260421.tgz \
  -C /home/DATN/oss-cad-suite-20260421 --strip-components=1
```

### 5. Patch ORFS nếu cần

```bash
python3 /home/DATN/tools/patch_orfs_compat.py
```

### 6. Chạy baseline flow

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  -j1
```

## Tiêu chí hoàn thành

- ORFS chạy qua các bước chính
- sinh được artifact vật lý thật
- có thể dùng OpenROAD làm backend đánh giá cho các bước placement sau này

