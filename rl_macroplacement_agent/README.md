# RL Macroplacement Agent

Thư mục này giữ lại phần lõi của flow RL hiện tại:

- `obs_features.py`: tạo observation/state từ `netlist.pb.txt` và `.plc`
- `policy_model.py`: actor-critic graph-based
- `ppo_agent.py`: PPO update, GAE, loss
- `train_ppo.py`: train
- `eval_policy.py`: chạy policy đã train và lưu `.plc`
- `eval_proxy.py`: đo proxy cost từ `PlacementCost`
- `plc_to_openroad_tcl.py`: đổi `.plc` sang Tcl để xem/eval trong OpenROAD
- `run_dreamplace_baseline.py`: baseline DREAMPlace
- `convert_bookshelf_pl_to_plc.py`: đổi output DREAMPlace `.pl` sang `.plc`

## Đầu vào trực tiếp cho RL

Flow train/eval hiện tại cần:

- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt`
- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial_safe.plc`

Tùy chọn để đối chiếu:

- `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc`

## Cost đang tối ưu

Flow PPO hiện tại tối ưu đúng theo proxy cost mặc định của MacroPlacement:

```text
proxy_cost = 1.0 * wirelength_cost + 0.5 * density_cost + 0.5 * congestion_cost
```

Ba weight này có thể đổi trực tiếp bằng:

- `--wirelength_weight`
- `--density_weight`
- `--congestion_weight`

## Reward mặc định

Theo hướng AlphaChip / Google Circuit Training, reward mặc định là reward cuối
episode dựa trên proxy cost placement cuối:

```text
terminal_reward = -final_proxy_cost
```

Trong repo này:

- Các step trung gian có reward `0.0`
- Step cuối episode dùng `-final_cost`
- Invalid action giữ penalty riêng, mặc định `-4.0`
- `initial_cost` chỉ dùng để log baseline và so sánh, không dùng làm RL reward

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

## Chạy tay tối thiểu cho ariane133

Nếu chưa có `initial_safe.plc`, tạo một lần:

```bash
python openroad_docker_lab/scripts/fix_plc.py \
  --input MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --output MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial_safe.plc \
  --margin_grid_cells 1
```

Chạy train seed 1:

```bash
mkdir -p experiments/ariane133_safe/seed_1

python rl_macroplacement_agent/scripts/train_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial_safe.plc \
  --out_dir experiments/ariane133_safe/seed_1 \
  --episodes 20 \
  --rollout_episodes 4 \
  --max_macros 133 \
  --max_nodes 1024 \
  --max_edges 4000 \
  --max_grid 32 \
  --wirelength_weight 1.0 \
  --density_weight 0.5 \
  --congestion_weight 0.5 \
  --batch_size 1 \
  --seed 1 \
  --device cuda | tee experiments/ariane133_safe/seed_1/train.log
```

Đổi `seed_1` thành `seed_2`, `seed_3` và đổi `--seed` tương ứng để có nhiều lần chạy.

Đọc kết quả:

```bash
cat experiments/ariane133_safe/seed_1/alphachip_like_train_summary.json
```

So sánh 3 seed:

```bash
python - <<'PY'
import json
from pathlib import Path

for p in sorted(Path("experiments/ariane133_safe").glob("seed_*/alphachip_like_train_summary.json")):
    data = json.loads(p.read_text())
    init_cost = data["last_episode"]["initial_cost"]
    best_cost = data["best_cost"]
    final_cost = data["last_episode"]["final_cost"]
    best_improve = (init_cost - best_cost) / init_cost * 100
    print(p.parent.name, "best_improve =", f"{best_improve:.4f}%")
    print("  initial_cost =", init_cost)
    print("  best_cost    =", best_cost)
    print("  final_cost   =", final_cost)
    print("  wirelength   =", data["last_episode"]["wirelength"])
    print("  density_cost =", data["last_episode"]["density_cost"])
    print("  congestion   =", data["last_episode"]["congestion_cost"])
PY
```

Nếu `best_cost < initial_cost` thì seed đó đã chứng minh RL tìm được placement tốt hơn placement ban đầu.

## Train PPO

Trên máy GPU, sau khi kích hoạt `rl_env`, có thể dùng script cấu hình sẵn để
giảm VRAM:

```bash
source rl_env/bin/activate
EPISODES=10 ROLLOUT_EPISODES=2 BATCH_SIZE=1 MAX_EDGES=4000 \
  ./rl_macroplacement_agent/scripts/run_ariane133.sh
```

Các biến `EPISODES`, `ROLLOUT_EPISODES`, `BATCH_SIZE`, `MAX_NODES`,
`MAX_EDGES`, `MAX_GRID`, `MAX_MACROS`, `WIRELENGTH_WEIGHT`,
`DENSITY_WEIGHT`, `CONGESTION_WEIGHT`, `DEVICE` và `OUT_DIR` đều có thể đổi
trực tiếp trước lệnh.

Hoặc gọi Python thủ công:

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

Test tối thiểu:

```bash
python rl_macroplacement_agent/scripts/train_ppo.py \
  --netlist <path_to_netlist.pb.txt> \
  --init_plc <path_to_initial.plc> \
  --out_dir /tmp/ppo_ct_smoke \
  --episodes 2 \
  --rollout_episodes 1
```

## Evaluate policy

```bash
python rl_macroplacement_agent/scripts/eval_policy.py \
  --model rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/train/alphachip_like_actor_critic.pt \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial_safe.plc \
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

- `train_ppo.py`, `eval_policy.py`, `ppo_agent.py`, `policy_model.py`, `obs_features.py`
- `eval_proxy.py`
- `convert_bookshelf_pl_to_plc.py`
- `run_dreamplace_baseline.py`
- `plc_to_openroad_tcl.py`
- `inspect_*`
