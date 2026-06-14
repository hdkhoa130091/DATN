# RL Macroplacement Agent

Thư mục này giữ lại phần lõi của flow RL hiện tại:

- `alphachip_like_features.py`: tạo observation/state từ `netlist.pb.txt` và `.plc`
- `alphachip_like_model.py`: actor-critic graph-based
- `alphachip_like_agent.py`: PPO update, GAE, loss
- `train_alphachip_like_ppo.py`: train
- `evaluate_alphachip_like_policy.py`: chạy policy đã train và lưu `.plc`
- `eval_proxy.py`: đo proxy cost từ `PlacementCost`
- `plc_to_openroad_tcl.py`: đổi `.plc` sang Tcl để xem/eval trong OpenROAD
- `run_dreamplace_baseline.py`: baseline DREAMPlace
- `convert_bookshelf_pl_to_plc.py`: đổi output DREAMPlace `.pl` sang `.plc`

## Đầu vào trực tiếp cho RL

Flow train/eval hiện tại cần:

- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt`
- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc`

Tùy chọn để đối chiếu:

- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc`

## Setup

```bash
python3 -m venv rl_env
source rl_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r rl_macroplacement_agent/requirements.txt
```

Nếu dùng DREAMPlace:

```bash
bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Script này tự dò CUDA. Có GPU/CUDA thì build bản GPU, không có thì build CPU bình thường.

## Train AlphaChip-like PPO

Trên máy GPU, sau khi kích hoạt `rl_env`, có thể dùng script cấu hình sẵn để
giảm VRAM:

```bash
source rl_env/bin/activate
EPISODES=10 ROLLOUT_EPISODES=2 BATCH_SIZE=1 MAX_EDGES=4000 \
  ./rl_macroplacement_agent/scripts/run_ariane133_ppo.sh
```

Các biến `EPISODES`, `ROLLOUT_EPISODES`, `BATCH_SIZE`, `MAX_NODES`,
`MAX_EDGES`, `MAX_GRID`, `MAX_MACROS`, `DEVICE` và `OUT_DIR` đều có thể đổi
trực tiếp trước lệnh.

Hoặc gọi Python thủ công:

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

## Evaluate policy

```bash
python rl_macroplacement_agent/scripts/evaluate_alphachip_like_policy.py \
  --model rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/train/alphachip_like_actor_critic.pt \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval \
  --max_macros 5 \
  --max_nodes 1024 \
  --max_edges 10000 \
  --max_grid 32 \
  --deterministic
```

Đầu ra chính:

- `alphachip_like_actor_critic.pt`
- `alphachip_like_training_history.csv`
- `alphachip_like_train_summary.json`
- `alphachip_like_final.plc`
- `alphachip_like_eval_summary.json`

## DREAMPlace baseline

```bash
python rl_macroplacement_agent/scripts/run_dreamplace_baseline.py \
  --dreamplace_root DREAMPlace \
  --json DREAMPlace/test/ispd2005/adaptec1.json \
  --out_dir rl_macroplacement_agent/results/dreamplace/adaptec1
```

Nếu muốn so cùng benchmark RL:

```bash
python rl_macroplacement_agent/scripts/convert_bookshelf_pl_to_plc.py \
  --dreamplace_pl path/to/dreamplace_output.pl \
  --template_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --out rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace.plc

python rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace.plc \
  --out rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace_metrics.json
```

## Chuyển placement RL sang OpenROAD

```bash
python rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py \
  --in_tcl rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final_raw.tcl \
  --out_tcl rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final_openroad.tcl
```

## Cấu trúc nên giữ

Nên tập trung vào:

- `alphachip_like_*`
- `eval_proxy.py`
- `convert_bookshelf_pl_to_plc.py`
- `run_dreamplace_baseline.py`
- `plc_to_openroad_tcl.py`
- `inspect_*`
