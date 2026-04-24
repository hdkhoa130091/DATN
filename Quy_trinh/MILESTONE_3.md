# Milestone 3 - Xây RL Loop Open-Source Thay Thế AlphaChip

## Mục tiêu

Milestone 3 không nhằm chạy Google AlphaChip full system.

Milestone này có mục tiêu thực tế hơn:

- xây một vòng lặp RL macro placement bằng công cụ open-source
- dùng dữ liệu từ `MacroPlacement`
- dùng `plc_client_os` làm proxy evaluator
- train một agent đơn giản bằng `Gymnasium + Stable-Baselines3`

## Vì sao không đi tiếp theo AlphaChip gốc

Trong môi trường hiện tại, không thể chạy AlphaChip đầy đủ vì:

- `plc_wrapper_main` không public
- backend đánh giá kiểu Google internal không có
- repo `circuit_training` không tự đủ để tạo lại toàn bộ AlphaChip
- hạ tầng distributed training và bộ cost engine production không có

Do đó, milestone 3 chính là bước chuyển hướng chính thức:

```text
Không cố tái tạo AlphaChip full
-> dựng AlphaChip-like open-source research flow
```

## Thành phần thay thế open-source

| Thành phần AlphaChip | Thay thế trong đồ án |
|---|---|
| RL training infra | `Gymnasium`, `stable-baselines3`, `sb3-contrib` |
| PPO/distributed RL | `MaskablePPO` chạy local |
| `plc_wrapper_main` | `MacroPlacement/CodeElements/Plc_client/plc_client_os.py` |
| internal cost backend | `get_cost()`, `get_wirelength()`, `get_density_cost()` |
| production dataset | benchmark `MacroPlacement` |

## Kiến trúc milestone 3

```text
netlist.pb.txt + initial.plc
    -> PlacementCost / plc_client_os
    -> Gymnasium environment
    -> MaskablePPO
    -> reward history
    -> best_rl.plc
    -> best_proxy.json
```

## Thư mục làm việc mới

```bash
/home/DATN/rl_macroplacement_agent
```

Không sửa trực tiếp third-party repo trừ khi thật sự cần:

- `/home/DATN/MacroPlacement`
- `/home/DATN/circuit_training`
- `/home/DATN/OpenROAD-flow-scripts`

## File chính của milestone 3

- [ariane133_ng45.yaml](/home/DATN/rl_macroplacement_agent/configs/ariane133_ng45.yaml)
- [inspect_dataset.py](/home/DATN/rl_macroplacement_agent/scripts/inspect_dataset.py)
- [eval_proxy.py](/home/DATN/rl_macroplacement_agent/scripts/eval_proxy.py)
- [plc_utils.py](/home/DATN/rl_macroplacement_agent/scripts/plc_utils.py)
- `macro_env.py`
- `train_maskable_ppo.py`
- `evaluate_policy.py`
- `plot_training.py`

## Reward và evaluator

Reward version đầu nên dùng:

```text
reward = (previous_cost - current_cost) * reward_scale
```

Ở milestone 3:

- `get_cost()` là reward chính
- congestion là optional
- không để pipeline chết vì `get_congestion_cost()`

## Quy trình thực hiện

### 1. Tạo thư mục dự án RL

```bash
mkdir -p /home/DATN/rl_macroplacement_agent/{configs,scripts,results/proxy,results/ppo,results/openroad,results/figures,logs,docs}
```

### 2. Chạy baseline proxy

Chạy lại các lệnh của milestone 2 để chắc dữ liệu ổn.

### 3. Dùng `plc_utils.py` để đọc/ghi `.plc`

```bash
python3 /home/DATN/rl_macroplacement_agent/scripts/plc_utils.py \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --summary
```

### 4. Viết `macro_env.py`

Environment tối giản:

- action: chọn grid cell
- state: vector đơn giản
- reward: delta cost
- done: đặt xong số macro mục tiêu

### 5. Viết `train_maskable_ppo.py`

Chạy smoke test trước:

```bash
python3 train_maskable_ppo.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45 \
  --steps 1000 \
  --max_macros 20
```

Sau khi smoke test ổn mới tăng lên `20000` steps.

## Tiêu chí hoàn thành

- RL loop chạy được ít nhất `1000` timesteps
- có `reward_history.csv`
- có `best_rl.plc`
- có `best_proxy.json`

## Điều không được hiểu sai

Thành công của milestone 3 không có nghĩa là:

- tái tạo được AlphaChip của Google
- vượt `legalized.plc` ngay lập tức

Thành công thực sự của milestone 3 là:

- chứng minh được RL loop open-source hoạt động trên bài toán macro placement
