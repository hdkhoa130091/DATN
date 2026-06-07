# DATN-1

Repo này đã được tinh gọn để tập trung vào flow chính:

```text
MacroPlacement benchmark
-> netlist.pb.txt + initial.plc
-> RL macro placement (AlphaChip-like PPO)
-> final .plc
-> OpenROAD / proxy evaluation
```

## Thành phần chính còn lại

- `MacroPlacement/`
  - benchmark, translator, `PlacementCost`, các file `netlist.pb.txt`, `initial.plc`, `legalized.plc`
- `rl_macroplacement_agent/`
  - code RL chính
- `openroad_docker_lab/`
  - Docker để chạy OpenROAD và xem GUI
- `datn_docker_env/`
  - Docker cho môi trường RL / DreamPlace
- `bao_cao_hoc_tang_cuong_pandoc.md`
  - báo cáo hiện tại

## Flow dữ liệu ngắn gọn

### EDA trước RL

- RTL / netlist / DEF / LEF / metadata
- translator của `MacroPlacement`
- tạo:
  - `netlist.pb.txt`
  - `initial.plc`
  - `legalized.plc`

### RL

Script chính:

- `rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py`
- `rl_macroplacement_agent/scripts/evaluate_alphachip_like_policy.py`

Đầu vào trực tiếp:

- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt`
- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc`

### EDA sau RL

- convert `.plc` sang Tcl
- mở/evaluate trong OpenROAD

## Benchmark mặc định

```bash
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

File quan trọng:

```bash
netlist.pb.txt
initial.plc
legalized.plc
```

## OpenROAD GUI

Image hiện dùng:

```bash
openroad-docker-lab:latest
```

Mở GUI:

```bash
cd openroad_docker_lab
xhost +local:docker
./scripts/run_gui_x11.sh
```

Trong container:

```bash
openroad -gui
```

## RL train nhanh

```bash
python rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/train \
  --episodes 10 \
  --rollout_episodes 4 \
  --max_macros 5 \
  --max_nodes 1024 \
  --max_edges 10000 \
  --max_grid 32 \
  --device cpu
```

## Cây thư mục nên quan tâm

```text
rl_macroplacement_agent/scripts/alphachip_like_features.py
rl_macroplacement_agent/scripts/alphachip_like_model.py
rl_macroplacement_agent/scripts/alphachip_like_agent.py
rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py
rl_macroplacement_agent/scripts/evaluate_alphachip_like_policy.py
rl_macroplacement_agent/scripts/eval_proxy.py
rl_macroplacement_agent/scripts/run_dreamplace_baseline.py
rl_macroplacement_agent/scripts/convert_bookshelf_pl_to_plc.py
rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py
```

## Ghi chú

- Repo đã bỏ nhánh `MaskablePPO` cũ và các tài liệu trùng lặp cấp repo.
- `install_dreamplace.sh` tự dò GPU/CUDA; không cần giữ riêng flow CPU-only và GPU-only.
