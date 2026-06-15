# OpenROAD Docker Lab

Mục tiêu của thư mục này là build một Docker image hoàn chỉnh để khi vào
container có thể dùng ngay:

- `yosys`
- `yosys-abc`
- `abc`
- `openroad`
- `klayout`
- `python3`
- `git`

## Quy trình chuẩn

### 1. Build image

```bash
cd /path/to/DATN
./openroad_docker_lab/scripts/build.sh
```

Image được tạo với tên:

```text
openroad-docker-lab:latest
```

### 2. Vào container

```bash
./openroad_docker_lab/scripts/run_cli.sh
```

Container mount repo vào:

```text
/workspace/DATN
```

### 3. Kiểm tra tool

Trong container:

```bash
cd /workspace/DATN/openroad_docker_lab
./scripts/test_tools.sh
```

Nếu build đúng, các lệnh sau phải chạy được trực tiếp trên `PATH`:

```bash
yosys -V
yosys-abc -h
abc -h
openroad -version
klayout -v
python3 --version
git --version
```

## Image build những gì

Dockerfile cài và build:

- `oss-cad-suite`
- symlink `yosys`, `yosys-abc`, `abc` vào `/usr/local/bin`
- OpenROAD build từ source
- OpenROAD-flow-scripts
- `klayout`

Vì vậy sau khi build lại image, `test_tools.sh` không còn tình trạng
`yosys not found` hoặc `abc not found`.

## Khi sửa Dockerfile

Nếu đã sửa Dockerfile, cần build lại image:

```bash
cd /path/to/DATN
./openroad_docker_lab/scripts/build.sh
```

Nếu container cũ đang tồn tại, xóa nó rồi chạy lại:

```bash
docker rm -f openroad_cli
./openroad_docker_lab/scripts/run_cli.sh
```

## Synthesis và ORFS

Hướng dẫn synthesis, floorplan, placement và ví dụ Ariane133 nằm ở:

```text
openroad_docker_lab/SYNTHESIS_GUIDE.md
```
