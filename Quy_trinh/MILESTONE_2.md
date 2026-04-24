# Milestone 2 - Chuẩn Hóa Dữ Liệu Cho RL Macro Placement

## Mục tiêu

Milestone 2 có nhiệm vụ chuyển từ artifact EDA hoặc benchmark có macro sang dữ liệu chuẩn mà pipeline placement/RL có thể đọc được.

Ở milestone này, mục tiêu là:

- chọn benchmark có macro thật
- dùng dữ liệu và công cụ có sẵn trong `MacroPlacement`
- chuẩn hóa đầu vào theo format kiểu `circuit_training`
- kiểm tra dữ liệu bằng `PlacementCost` hoặc `plc_client`

## Kết luận kỹ thuật cần nhớ

Không dùng `gcd` làm benchmark chính cho RL vì `gcd` không có macro thật.

Benchmark nên ưu tiên:

- `ariane133`
- `ariane136`
- `nvdla`
- `mempool`

Trong môi trường hiện tại, testcase đầu tiên nên dùng:

```bash
/home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

## Dữ liệu đầu vào chính

- `LEF`
- `DEF`
- `SDC`
- `SPEF`
- benchmark có macro thật
- dữ liệu mẫu trong `MacroPlacement`

## Dữ liệu đầu ra chính

- `netlist.pb.txt`
- `initial.plc`
- `legalized.plc`

## Công cụ sử dụng

- `MacroPlacement/CodeElements/FormatTranslators`
- `MacroPlacement/CodeElements/CodeFlowIntegration`
- `MacroPlacement/CodeElements/Plc_client`
- `circuit_training/docs/NETLIST_FORMAT.md`
- `circuit_training/docs/PLACEMENT_COST.md`

## Quy tắc vận hành quan trọng

### 1. Không dùng file demo để train thật

Không dùng:

```bash
/home/DATN/MacroPlacement/Flows/util/netlist.pb.txt
```

File này chỉ phù hợp cho demo translator và có thể gây lỗi như:

- `MACRO pins not found`
- `KeyError: 'g9'`

### 2. Ưu tiên dataset Ariane đã chuẩn hóa sẵn

Dùng trước:

```bash
/home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

### 3. Kiểm tra dữ liệu bằng `PlacementCost`

Mục tiêu của milestone 2 là chứng minh:

- `netlist.pb.txt` đọc được
- `.plc` khôi phục được
- proxy cost tính được

## Quy trình thực hiện

### 1. Kiểm tra bộ dữ liệu

```bash
ls -lh /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
ls -lh /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
ls -lh /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc
```

### 2. Tạo env Python cho RL flow

```bash
cd /home/DATN
python3 -m venv rl_env
source rl_env/bin/activate
pip install --upgrade pip
pip install absl-py numpy pandas matplotlib pyyaml gymnasium stable-baselines3 sb3-contrib
```

### 3. Thiết lập `PYTHONPATH`

```bash
export PYTHONPATH=/home/DATN/MacroPlacement/CodeElements/Plc_client:/home/DATN/circuit_training:/home/DATN/MacroPlacement:$PYTHONPATH
```

### 4. Kiểm tra bằng script inspect

```bash
python3 /home/DATN/rl_macroplacement_agent/scripts/inspect_dataset.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --initial_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --legalized_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc \
  --out /home/DATN/rl_macroplacement_agent/results/proxy/ariane133_ng45/dataset_inspect.json
```

### 5. Chạy baseline proxy

```bash
python3 /home/DATN/rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out /home/DATN/rl_macroplacement_agent/results/proxy/ariane133_ng45/initial.json
```

```bash
python3 /home/DATN/rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc \
  --out /home/DATN/rl_macroplacement_agent/results/proxy/ariane133_ng45/legalized.json
```

## Trạng thái đã kiểm chứng trong workspace

- dataset `ariane133` có đủ `netlist.pb.txt`, `initial.plc`, `legalized.plc`
- `PlacementCost` hiện đọc đúng metadata `.plc`
- baseline proxy đã chạy được

## Tiêu chí hoàn thành

- có `dataset_inspect.json`
- có `initial.json`
- có `legalized.json`
- dữ liệu sẵn sàng cho RL loop

## Chuyển tiếp sang milestone 3

Sau milestone 2, hướng đúng không phải là cố chạy AlphaChip full.

Hướng đúng là:

- giữ lại data/format của `MacroPlacement + circuit_training`
- thay RL infra bằng open-source RL stack
- thay cost engine không public bằng `plc_client_os`
