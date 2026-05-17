# Next Session Checklist

Dùng file này khi quay lại dự án trên một máy SSH mới hoặc Docker GPU image mới.
Mục tiêu là **khôi phục môi trường đúng**, **xác nhận pipeline còn sạch**, rồi mới tiếp tục thí nghiệm dài.

## 1. Đọc nhanh trước khi làm

```text
README.md
RESULTS.md
PROGRESS.md
```

Nếu cần chi tiết setup/build:

```text
BUILD_GUIDE.md
FULL_OPEN_SOURCE_RTL_TO_RL_GUIDE.md
AGENT_RL_MACROPLACEMENT_OPEN_SOURCE_FLOW.md
```

## 2. Kiểm tra repo

```bash
cd /home/DATN
git status
git branch --show-current
git pull --ff-only
```

Nếu clone mới:

```bash
git clone <repo-url> DATN
cd DATN
```

## 3. Kiểm tra máy GPU / CUDA

```bash
nvidia-smi || true
nvcc --version || true
python3 --version
```

Ghi lại:

- GPU model
- NVIDIA driver
- CUDA toolkit
- Python version

## 4. Dựng môi trường nếu là máy mới

```bash
bash rl_macroplacement_agent/scripts/install_system_deps_ubuntu.sh

python3 -m venv rl_env
source rl_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r rl_macroplacement_agent/requirements.txt
```

Kiểm tra thư mục benchmark chính có đủ file:

```bash
ls MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

Cần có ít nhất:

```text
netlist.pb.txt
initial.plc
legalized.plc
```

## 5. Build / kiểm tra DREAMPlace

```bash
source rl_env/bin/activate
bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Nếu muốn smoke test:

```bash
RUN_SMOKE_TEST=1 bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Nhớ:

- CUDA 12.x cần patch CUB; script build đã tự xử lý.
- Nếu build fail với `gmake Error 2`, đọc lỗi compiler **ở phía trên**, không chỉ nhìn dòng cuối.

## 6. Kiểm tra OpenROAD / ORFS

```bash
openroad -version || true
```

Sanity flow nếu cần:

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  synth floorplan place -j1
```

## 7. Bắt buộc smoke-test AlphaChip-like trước khi train dài

```bash
cd /home/DATN
source rl_env/bin/activate

python rl_macroplacement_agent/scripts/inspect_alphachip_like_features.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --max_macros 5 \
  --run_model \
  --out rl_macroplacement_agent/results/alphachip_like_smoke/ariane133_macros5.json
```

Kỳ vọng chính:

```text
feature_nodes: 929
hard_macros: 133
soft_macros: 782
port_clusters: 14
nonzero_edges: 9576
```

## 8. Những lỗi không được để quay lại

- Advantage phải normalize trên **combined rollout batch**, không normalize riêng từng episode.
- Trước mỗi AlphaChip-like episode phải có `unplace_all_nodes()`.
- `get_congestion_cost()` hiện có thể lỗi; chưa dùng nó làm metric bắt buộc.
- Không dùng `cur001` để kết luận khoa học.
- Không đánh giá graph model chỉ bằng bài 5 macro nhỏ.

## 9. Trạng thái nghiên cứu hiện tại

| Seed | Method at 20 macros | Eval cost | Wirelength |
|---:|---|---:|---:|
| 1 | curriculum 5 -> 10 -> 20 | 0.0544441094 | 3524933.8925 |
| 1 | scratch 20 | 0.0610056629 | 3949755.6562 |
| 2 | curriculum 5 -> 10 -> 20 | 0.0533384836 | 3453351.1676 |
| 2 | scratch 20 | 0.0557189124 | 3607469.8480 |

Đã có 2 seed sạch cho thấy curriculum tốt hơn scratch. Cần thêm seed 3 để tạo bảng `mean ± std` chính thức.

## 10. Việc cần làm tiếp theo ngay

### Bước kế tiếp của nghiên cứu

```bash
cd /home/DATN
source rl_env/bin/activate

bash rl_macroplacement_agent/scripts/run_alphachip_like_curriculum.sh \
  NanGate45 ariane133 cur005 3 615 5,10,20
```

Nếu curriculum script dừng trước scratch final stage, chạy scratch 20 macro cùng seed bằng lệnh manual tương ứng rồi báo lại để tổng hợp.

### Sau khi có seed 3

1. Tổng hợp bảng `curriculum vs scratch` 20 macro với `mean ± std`.
2. Nếu kết quả vẫn tốt, mở rộng:

```text
5 -> 10 -> 20 -> 50 -> 100 -> 133 hard macros
```

3. Sau đó đưa placement RL vào OpenROAD / P&R flow để tạo bảng vật lý gần phong cách `MacroPlacement`:

```text
wirelength, power, WNS, TNS, congestion
preCTS / postCTS / postRoute
```

## 11. File cần xem khi muốn mở placement bằng OpenROAD

Các run manual và curriculum mới sinh sẵn:

```text
openroad/alphachip_like_final_raw.tcl
openroad/alphachip_like_final_openroad.tcl
openroad/view_alphachip_like_final.tcl
```

Mở GUI:

```bash
openroad -gui
```

sau đó source file `view_alphachip_like_final.tcl` của run cần xem.

---

Nếu chỉ có 10 phút để nhớ lại dự án, hãy đọc theo thứ tự:

```text
NEXT_SESSION_CHECKLIST.md -> RESULTS.md -> PROGRESS.md
```
