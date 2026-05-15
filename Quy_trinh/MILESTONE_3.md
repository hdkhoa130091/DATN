# Milestone 3 - Xây RL Loop Open-Source Thay Thế AlphaChip

## Mục tiêu

Milestone 3 không nhằm chạy Google AlphaChip full system.

Milestone này có mục tiêu thực tế hơn:

- xây một vòng lặp RL macro placement bằng công cụ open-source
- dùng dữ liệu từ `MacroPlacement`
- dùng `plc_client_os` làm proxy evaluator
- train một agent đơn giản bằng `Gymnasium + Stable-Baselines3`
- dựng DREAMPlace làm baseline gradient-based để có đối chứng khi đánh giá RL

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
| baseline placement đối chứng | `DREAMPlace` |

## Kiến trúc milestone 3

```text
netlist.pb.txt + initial.plc
    -> PlacementCost / plc_client_os
    -> Gymnasium environment
    -> MaskablePPO
    -> reward history
    -> best_rl.plc
    -> best_proxy.json

DREAMPlace
    -> `.pl` baseline
    -> convert về `.plc` nếu cùng benchmark
    -> chấm bằng cùng PlacementCost để so sánh với RL
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
- `install_dreamplace.sh`
- `run_dreamplace_baseline.py`
- `convert_bookshelf_pl_to_plc.py`
- `compare_results.py`


## Nhánh baseline DREAMPlace

DREAMPlace không thay thế agent RL trong milestone này. Nó dùng để trả lời câu hỏi đối chứng:

```text
Agent RL của đồ án tốt hơn hay kém hơn một placer tối ưu hóa truyền thống trên cùng cách chấm điểm?
```

### Khi nào cần DREAMPlace

- cần một baseline ngoài `initial.plc` và `legalized.plc`
- cần so sánh PPO / AlphaChip-like PPO với một placer gradient-based
- cần kiểm chứng pipeline convert đầu ra placement về evaluator chung

### Cài và build nhanh

Repo đã có script cài đặt và script này build theo đường đã kiểm chứng `DREAMPlace/install`:

```bash
cd /home/DATN
source rl_env/bin/activate
bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Nếu muốn chạy smoke test ngay sau build, dùng:

```bash
RUN_SMOKE_TEST=1 bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Nếu cần làm thủ công hoặc xử lý lỗi build, đọc phần `DREAMPlace Build And Run` trong:

```text
/home/DATN/BUILD_GUIDE.md
```

Bản hướng dẫn đã ghi rõ:

- dependency hệ thống và Python cần thêm, bao gồm `tcl` để có executable `tclsh` cho OpenTimer
- cách clone `--recursive`
- cách build bằng CMake
- vì sao nên chạy từ cây `install/`
- cách tạo config CPU khi build không có CUDA
- cách tải benchmark ISPD2005 và chạy `adaptec1` để smoke test

### Smoke test build/run

Chạy trực tiếp qua wrapper của repo:

```bash
python3 /home/DATN/rl_macroplacement_agent/scripts/run_dreamplace_baseline.py \
  --dreamplace_root /home/DATN/DREAMPlace/install \
  --json /home/DATN/rl_macroplacement_agent/results/dreamplace/adaptec1/adaptec1_cpu.json \
  --out_dir /home/DATN/rl_macroplacement_agent/results/dreamplace/adaptec1_script_run
```

Đầu ra tối thiểu cần có:

```text
dreamplace_run_summary.json
adaptec1.gp.pl
```

### Điều kiện để so sánh công bằng với RL

Chạy `adaptec1` chỉ chứng minh DREAMPlace build/run được. Muốn so sánh với agent RL trên `ariane133`, phải:

1. tạo config DREAMPlace cho **cùng thiết kế**
2. lấy đầu ra `.pl` của DREAMPlace
3. convert về `.plc` bằng cùng template/netlist của `ariane133`
4. chấm lại bằng `eval_proxy.py` / `PlacementCost`

Ví dụ bước convert và chấm:

```bash
python3 /home/DATN/rl_macroplacement_agent/scripts/convert_bookshelf_pl_to_plc.py \
  --dreamplace_pl path/to/dreamplace_output.pl \
  --template_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --out /home/DATN/rl_macroplacement_agent/results/dreamplace/ariane133_ng45/dreamplace.plc

python3 /home/DATN/rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/rl_macroplacement_agent/results/dreamplace/ariane133_ng45/dreamplace.plc \
  --out /home/DATN/rl_macroplacement_agent/results/dreamplace/ariane133_ng45/dreamplace_metrics.json
```

Khi đó mới dùng `compare_results.py` để so sánh với kết quả PPO.

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
- DREAMPlace build/run được ít nhất trên smoke test chính thức
- nếu làm so sánh cùng benchmark, có thêm `dreamplace_metrics.json` sau khi convert về `.plc`

## Điều không được hiểu sai

Thành công của milestone 3 không có nghĩa là:

- tái tạo được AlphaChip của Google
- vượt `legalized.plc` ngay lập tức

Thành công thực sự của milestone 3 là:

- chứng minh được RL loop open-source hoạt động trên bài toán macro placement
- có baseline DREAMPlace để kết quả RL không bị đánh giá trong chân không
