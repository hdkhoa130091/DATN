# DATN-1

Repo này đã được tinh gọn để tập trung vào flow chính:

```text
MacroPlacement benchmark
-> netlist.pb.txt + initial.plc
-> RL macro placement (AlphaChip-like PPO)
-> final .plc
-> OpenROAD / proxy evaluation
```

## Tài liệu chính

- [Huong_dan_Pipeline.md](Huong_dan_Pipeline.md)
  - hướng dẫn đầy đủ từ ORFS, `flow.py`, train/eval RL, convert Tcl, OpenROAD GUI
- [artifacts/practical_macro_soc_50/run_1/README.md](artifacts/practical_macro_soc_50/run_1/README.md)
  - bộ artifact đã chạy sẵn cho `practical_macro_soc_50` với `run_1`

## Thành phần chính còn lại

- `MacroPlacement/`
  - benchmark, translator, `PlacementCost`, các file `netlist.pb.txt`, `initial.plc`, `legalized.plc`
- `rl_macroplacement_agent/`
  - code RL chính
- `openroad_docker_lab/`
  - Docker để chạy OpenROAD và xem GUI
- `artifacts/`
  - nơi lưu các kết quả đã chạy sẵn, gọn và đủ dùng để tái hiện

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

- `rl_macroplacement_agent/scripts/train_ppo.py`
- `rl_macroplacement_agent/scripts/eval_policy.py`

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
./scripts/run_gui.sh
```

Trong container:

```bash
openroad -gui
```

## RL train nhanh

```bash
python rl_macroplacement_agent/scripts/train_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial_safe.plc \
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
rl_macroplacement_agent/scripts/obs_features.py
rl_macroplacement_agent/scripts/policy_model.py
rl_macroplacement_agent/scripts/ppo_agent.py
rl_macroplacement_agent/scripts/train_ppo.py
rl_macroplacement_agent/scripts/eval_policy.py
rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py
```

## Ghi chú

- `README.md` vẫn là trang hiển thị đầu repo trên GitHub.
- Tài liệu pipeline đầy đủ đã được chuyển thành `Huong_dan_Pipeline.md` ở đầu repository.
