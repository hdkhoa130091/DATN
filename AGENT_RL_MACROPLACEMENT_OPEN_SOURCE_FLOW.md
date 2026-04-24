# AGENT SPEC: Hướng 1 DATN - Open-source AlphaChip-like Flow bằng MacroPlacement + RL + OpenROAD

> File này được viết để mở trực tiếp trong VS Code / Windsurf / Codex.  
> Mục tiêu: cho agent đọc, hiểu bối cảnh, không đi sai hướng, và triển khai từng bước một flow **học tăng cường cho macro placement** ở mức open-source.

---

## 0. Tóm tắt nhiệm vụ cho agent

Bạn đang làm trong repo DATN tại:

```bash
/home/DATN
```

Mục tiêu của hướng 1 là dựng một flow thực dụng bằng công cụ có sẵn:

```text
OpenROAD / ORFS / Yosys
+ MacroPlacement
+ Circuit Training-style data
+ RL open-source thay thế phần AlphaChip không public
+ đưa kết quả placement quay lại OpenROAD để kiểm chứng
```

Không được hiểu nhầm rằng cần chạy Google AlphaChip full system. AlphaChip full system cần các thành phần không public hoặc không khả dụng trong môi trường hiện tại, đặc biệt là `plc_wrapper_main` và backend cost/evaluation đầy đủ.

Flow mục tiêu của DATN là:

```text
MacroPlacement benchmark
    -> netlist.pb.txt + initial.plc + legalized.plc
    -> plc_client_os / PlacementCost proxy evaluator
    -> Gymnasium environment
    -> PPO / MaskablePPO RL agent
    -> best_rl.plc
    -> convert .plc sang OpenROAD Tcl / DEF
    -> OpenROAD refine/evaluate
    -> so sánh proxy cost và QoR vật lý
```

---

## 1. Quy tắc vận hành bắt buộc

### 1.1. Không dùng giả định sai

Không được giả định có các tool sau:

```text
Cadence Genus
Cadence Innovus
Cadence Virtuoso
Google internal backend
Google TPU dataset
plc_wrapper_main public binary
```

Nếu cần thay thế:

```text
Genus      -> Yosys
Innovus    -> OpenROAD / OpenROAD-flow-scripts
AlphaChip cost engine -> MacroPlacement plc_client_os / PlacementCost
AlphaChip RL infra -> Stable-Baselines3 / sb3-contrib / Gymnasium
```

### 1.2. Không dùng file demo để train thật

Không dùng file này cho RL training chính:

```bash
/home/DATN/MacroPlacement/Flows/util/netlist.pb.txt
```

File này được tạo từ ví dụ translator demo và đã từng gây lỗi:

```text
MACRO pins not found
KeyError: 'g9'
```

Dataset nên dùng trước tiên:

```bash
/home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

Trong đó cần có:

```text
netlist.pb.txt
initial.plc
legalized.plc
```

### 1.3. Không phụ thuộc `plc_wrapper_main`

Trong môi trường hiện tại, tải `plc_wrapper_main` từ Google Cloud Storage trả về XML `AccessDenied`. Nếu thấy file `/usr/local/bin/plc_wrapper_main` chỉ khoảng 298 bytes và là XML, phải xóa nó:

```bash
rm -f /usr/local/bin/plc_wrapper_main
```

Dùng fallback open-source:

```text
/home/DATN/MacroPlacement/CodeElements/Plc_client/plc_client_os.py
```

### 1.4. Không lấy congestion làm điều kiện bắt buộc ban đầu

`get_cost()` đã chạy được với dataset đúng:

```text
get_cost: 0.04972213503402197
```

Nhưng `get_congestion_cost()` có thể lỗi:

```text
IndexError: list index out of range
```

Do đó trong milestone 3, reward chính dùng:

```text
proxy cost / wirelength-based cost
```

Congestion là optional, dùng `try/except`, không làm pipeline chết.

### 1.5. Không sửa trực tiếp third-party repo nếu chưa cần

Tạo code mới ở:

```bash
/home/DATN/rl_macroplacement_agent
```

Không sửa trực tiếp:

```bash
/home/DATN/MacroPlacement
/home/DATN/circuit_training
/home/DATN/OpenROAD-flow-scripts
```

trừ khi có ghi chú rõ trong commit.

---

## 2. Bối cảnh milestone hướng 1

### 2.1. Milestone 1 - Dựng nền EDA

Mục tiêu milestone 1:

```text
Dựng flow EDA open-source thay cho Genus/Innovus.
Chạy baseline physical design bằng OpenROAD-flow-scripts.
Sinh artifact vật lý thật để dùng tiếp.
```

Công cụ:

```text
Ubuntu 22.04
OpenROAD
OpenROAD-flow-scripts
Yosys từ OSS CAD Suite
KLayout
TigerVNC
Python 3.10+
```

Input chính:

```text
OpenROAD-flow-scripts
OpenROAD binary
OSS CAD Suite / Yosys
sample design nangate45/gcd
```

Output mong muốn:

```text
1_synth.*
2_floorplan.*
3_place.*
6_final.odb
6_final.def
6_final.sdc
6_final.v
6_final.spef
```

Ý nghĩa:

| Artifact | Ý nghĩa |
|---|---|
| `1_synth.*` | Netlist logic sau synthesis |
| `2_floorplan.*` | Floorplan, die/core, geometry ban đầu |
| `3_place.*` | Placement checkpoint |
| `6_final.*` | Thiết kế gần hoàn chỉnh sau route/fill, dùng để chứng minh flow EDA chạy được |

Trạng thái đã kiểm chứng theo milestone:

```text
Flow đã đi qua synth, floorplan, place, CTS, route, fill.
Đã tạo 6_final.*.
Có thể dừng ở final_report do lỗi GUI get_scenes, nhưng artifact chính vẫn đạt.
```

### 2.2. Milestone 2 - Chuẩn hóa dữ liệu cho RL

Mục tiêu milestone 2:

```text
Chuyển dữ liệu EDA / benchmark có macro sang format mà RL macroplacement đọc được.
```

Không dùng `gcd` làm benchmark RL vì `gcd` không có macro thật.

Benchmark nên dùng:

```text
ariane133
ariane136
nvdla
mempool
```

File quan trọng:

| File | Ý nghĩa | Tác dụng trong RL |
|---|---|---|
| `LEF` | Physical library, macro/cell size, pin/layer | Biết kích thước vật lý |
| `DEF` | Design placement, component, net, port | Có thể convert sang placement/netlist |
| `SDC` | Timing constraints | Dùng khi quay lại OpenROAD/timing |
| `SPEF` | Parasitic sau route | Đánh giá sâu sau implementation |
| `netlist.pb.txt` | Protobuf text netlist kiểu Circuit Training | Input chính của environment RL |
| `initial.plc` | Placement ban đầu | Reset state / baseline |
| `legalized.plc` | Placement hợp thức hóa / tối ưu có sẵn | Baseline đối chiếu |

Milestone 2 dùng các thành phần:

```text
MacroPlacement/CodeElements/FormatTranslators
MacroPlacement/CodeElements/Plc_client
circuit_training/docs/NETLIST_FORMAT.md
circuit_training/docs/PLACEMENT_COST.md
```

### 2.3. Milestone 3 - Chạy baseline placement hoặc RL

Mục tiêu milestone 3:

```text
Nạp dữ liệu đã chuẩn hóa vào environment hoặc placement loop.
Tính reward/cost.
Chạy baseline hoặc RL ngắn.
Lưu placement đầu ra, reward history, log.
```

Input:

```text
netlist.pb.txt
initial.plc
benchmark có macro thật
plc_client / PlacementCost
```

Output cần có:

```text
placement đầu ra (.plc)
log chạy
reward_history.csv
proxy cost JSON
hình placement nếu có
```

Lưu ý: Milestone 3 không yêu cầu tái tạo AlphaChip đầy đủ. Nó yêu cầu chứng minh pipeline placement/RL chạy được, quan sát được và có kết quả.

### 2.4. Milestone 4 - Đưa placement quay lại EDA

Mục tiêu milestone 4:

```text
Đưa placement từ RL/baseline quay lại OpenROAD để refine và đánh giá vật lý.
```

Input:

```text
best_rl.plc hoặc placement đầu ra
benchmark có macro
OpenROAD / ORFS flow
LEF/DEF/LIB/SDC tương ứng
```

Output:

```text
placement đã refine
OpenROAD reports
wirelength / congestion / timing nếu có
so sánh proxy cost vs physical QoR
```

---

## 3. AlphaChip cần gì và MacroPlacement thiếu gì?

### 3.1. AlphaChip full system gồm gì?

```text
1. RL model: Neural Network policy
2. RL algorithm: PPO training loop
3. Placement cost engine: plc_wrapper_main
4. EDA backend / evaluator mạnh
5. Dataset chip lớn
6. Distributed training infra
```

### 3.2. MacroPlacement có gì?

```text
1. Benchmark/testcases
2. Protobuf netlist / .plc placement
3. Translator / flow integration
4. Proxy cost implementation
5. plc_client_os fallback
6. Visualization
7. Baselines như simulated annealing / heuristic tools
```

### 3.3. MacroPlacement thiếu gì để thành AlphaChip?

| Thành phần | AlphaChip | MacroPlacement | Open-source thay thế đề xuất |
|---|---|---|---|
| RL model | Policy NN | Không có model đầy đủ | Stable-Baselines3 PPO / MaskablePPO |
| RL training loop | PPO distributed | Không có PPO loop hoàn chỉnh | Gymnasium env + SB3/sb3-contrib |
| Cost engine chính thức | `plc_wrapper_main` | `plc_client_os` fallback | Dùng `get_cost()`, patch/optional congestion |
| Backend vật lý | Internal / commercial EDA | Flow OpenROAD có sẵn nhưng không gắn RL loop | OpenROAD / ORFS |
| Dataset production | TPU/Google chip | Ariane/NVDLA/MemPool/ICCAD | Dùng MacroPlacement benchmark |
| Timing/routing feedback | Có hệ backend mạnh | Chưa phản hồi vào RL loop | OpenROAD report sau placement |

### 3.4. Kết luận kỹ thuật

Không thể chạy Google AlphaChip full system public trong môi trường này. Nhưng có thể dựng một flow tương tự ở mức nghiên cứu:

```text
MacroPlacement data
+ plc_client_os proxy cost
+ PPO/MaskablePPO open-source
+ OpenROAD verification
```

---

## 4. Kiến trúc flow đề xuất

```text
/home/DATN/MacroPlacement
    -> cung cấp benchmark, .pb.txt, .plc, proxy cost

/home/DATN/rl_macroplacement_agent
    -> code đồ án mới: env, train, eval, convert, report

/home/DATN/OpenROAD-flow-scripts
    -> kiểm chứng placement bằng physical implementation
```

Flow chi tiết:

```text
[MacroPlacement dataset]
    netlist.pb.txt
    initial.plc
    legalized.plc
        |
        v
[Proxy evaluator]
    plc_client_os / PlacementCost
    get_cost()
        |
        v
[Gymnasium RL Environment]
    state: placement + macro index + cost features
    action: chọn grid cell / macro move
    reward: delta cost hoặc -cost
        |
        v
[PPO / MaskablePPO]
    train ngắn
    lưu reward history
    lưu best_rl.plc
        |
        v
[OpenROAD integration]
    .plc -> Tcl / DEF
    place_cell hoặc macro placement Tcl
        |
        v
[EDA evaluation]
    OpenROAD reports
    compare with proxy cost
```

---

## 5. Cấu trúc thư mục cần tạo

Tạo thư mục mới:

```bash
mkdir -p /home/DATN/rl_macroplacement_agent/{configs,scripts,results/proxy,results/ppo,results/openroad,results/figures,logs,docs}
```

Cấu trúc mục tiêu:

```text
/home/DATN/rl_macroplacement_agent/
├── configs/
│   └── ariane133_ng45.yaml
├── scripts/
│   ├── eval_proxy.py
│   ├── inspect_dataset.py
│   ├── plc_utils.py
│   ├── macro_env.py
│   ├── train_maskable_ppo.py
│   ├── evaluate_policy.py
│   ├── plot_training.py
│   ├── plc_to_openroad_tcl.py
│   ├── run_openroad_eval.sh
│   └── compare_results.py
├── results/
│   ├── proxy/
│   ├── ppo/
│   ├── openroad/
│   └── figures/
├── logs/
└── docs/
```

---

## 6. Config chuẩn cho testcase đầu tiên

File:

```bash
/home/DATN/rl_macroplacement_agent/configs/ariane133_ng45.yaml
```

Nội dung đề xuất:

```yaml
design: ariane133
technology: NanGate45

workspace: /home/DATN
macroplacement_root: /home/DATN/MacroPlacement
circuit_training_root: /home/DATN/circuit_training
orfs_root: /home/DATN/OpenROAD-flow-scripts

benchmark_dir: /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping
netlist: /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
initial_plc: /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
legalized_plc: /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc

output_dir: /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45
proxy_result_dir: /home/DATN/rl_macroplacement_agent/results/proxy/ariane133_ng45
openroad_result_dir: /home/DATN/rl_macroplacement_agent/results/openroad/ariane133_ng45

reward:
  use_get_cost: true
  use_congestion: false
  invalid_action_penalty: -1.0
  no_improvement_penalty: -0.01
  reward_scale: 1000.0

rl:
  algorithm: MaskablePPO
  total_timesteps: 20000
  seed: 42
  max_macros: 20
  n_steps: 256
  batch_size: 64
  learning_rate: 0.0003
  gamma: 0.99
```

---

## 7. Bước 1 - Kiểm tra dataset

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/inspect_dataset.py
```

Mục tiêu:

```text
Xác nhận netlist.pb.txt, initial.plc, legalized.plc tồn tại.
In kích thước file.
In số macro/canvas/grid nếu đọc được.
Không crash nếu một chỉ số không đọc được.
```

Lệnh chạy thủ công:

```bash
cd /home/DATN

ls -lh /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
ls -lh /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
ls -lh /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc
```

Test bằng `plc_client_main.py`:

```bash
export PYTHONPATH=/home/DATN/circuit_training:/home/DATN/MacroPlacement:$PYTHONPATH

python3 /home/DATN/circuit_training/circuit_training/environment/plc_client_main.py \
  --netlist_file /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
```

Kết quả chấp nhận được:

```text
get_cost: <number>
```

Nếu crash ở congestion, vẫn chấp nhận cho milestone 3 nếu `get_cost` đã in ra trước.

---

## 8. Bước 2 - Đánh giá proxy cost cho baseline

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/eval_proxy.py
```

Yêu cầu script:

```text
Input:
  --netlist path/to/netlist.pb.txt
  --plc path/to/placement.plc
  --out path/to/result.json

Output:
  JSON gồm cost, wirelength nếu có, density nếu có, congestion nếu có hoặc error string.
```

Pseudo-code an toàn:

```python
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/DATN/MacroPlacement/CodeElements/Plc_client")
from plc_client_os import PlacementCost


def safe_call(name, fn):
    try:
        return {name: fn()}
    except Exception as e:
        return {name + "_error": repr(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--plc", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    plc = PlacementCost(args.netlist)
    plc.restore_placement(args.plc, ifInital=True, ifValidate=False)

    result = {
        "netlist": args.netlist,
        "plc": args.plc,
    }

    result.update(safe_call("cost", plc.get_cost))
    result.update(safe_call("wirelength", plc.get_wirelength))
    result.update(safe_call("density_cost", plc.get_density_cost))
    result.update(safe_call("congestion_cost", plc.get_congestion_cost))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

Chạy:

```bash
cd /home/DATN
export PYTHONPATH=/home/DATN/MacroPlacement/CodeElements/Plc_client:$PYTHONPATH

python3 rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out /home/DATN/rl_macroplacement_agent/results/proxy/ariane133_ng45/initial.json

python3 rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc \
  --out /home/DATN/rl_macroplacement_agent/results/proxy/ariane133_ng45/legalized.json
```

Đây là baseline số liệu trước khi train RL.

---

## 9. Bước 3 - Visualize placement

Dùng tool có sẵn:

```bash
cd /home/DATN/MacroPlacement/CodeElements/VisualPlacement

python3 visual_placement.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc

python3 visual_placement.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/legalized.plc
```

Nếu môi trường không có GUI, ghi nhận trong báo cáo:

```text
Tool đã đọc canvas/grid thành công.
Visualization cần VNC/X11 hoặc headless export bổ sung.
```

---

## 10. Bước 4 - Viết `plc_utils.py`

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/plc_utils.py
```

Mục tiêu:

```text
Đọc .plc text.
Lấy metadata: columns, rows, width, height.
Lấy danh sách node placement.
Ghi lại .plc sau khi sửa vị trí macro.
```

Định dạng dòng placement trong `.plc` thường là:

```text
<node_index> <x> <y> <orientation> <fixed>
```

Ví dụ logic cần hỗ trợ:

```python
class PlcFile:
    def __init__(self, path):
        self.path = path
        self.lines = []
        self.node_rows = {}
        self.columns = None
        self.rows = None
        self.width = None
        self.height = None

    def load(self):
        # parse lines
        # store line index for node rows
        pass

    def set_node_position(self, node_index, x, y, orientation=None, fixed=None):
        # rewrite exact node row
        pass

    def save(self, out_path):
        pass
```

Chú ý:

```text
Không được xóa comment header vì các dòng metadata như Columns/Rows/Width/Height quan trọng.
Giữ nguyên orientation/fixed nếu không thay đổi.
```

---

## 11. Bước 5 - Thiết kế environment RL

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/macro_env.py
```

### 11.1. Mục tiêu environment

Environment phải biến bài toán macro placement thành chuẩn RL:

| RL concept | Macro placement mapping |
|---|---|
| State | Placement hiện tại, macro đang đặt, cost hiện tại |
| Action | Chọn ô grid để đặt macro hoặc chọn move |
| Reward | `previous_cost - current_cost`, hoặc `-current_cost` |
| Done | Đặt xong số macro cần train |
| Invalid action | Out-of-bound, overlap rõ ràng, không nằm trong mask |

### 11.2. Action space đề xuất giai đoạn đầu

Không làm quá phức tạp ngay.

Dùng sequential macro placement:

```text
Episode reset ở initial.plc.
Mỗi step chọn vị trí grid cell cho macro thứ k.
Sau khi đặt macro k, k tăng lên.
Khi đặt xong max_macros thì done.
```

Action:

```text
Discrete(n_rows * n_cols)
```

Map:

```python
row = action // n_cols
col = action % n_cols
x = (col + 0.5) * (canvas_width / n_cols)
y = (row + 0.5) * (canvas_height / n_rows)
```

### 11.3. Observation giai đoạn đầu

Observation tối giản để chạy được:

```text
current_macro_index_normalized
previous_cost
x_normalized / y_normalized của một số macro đã đặt
macro_width_normalized / macro_height_normalized nếu lấy được
```

Nếu chưa lấy được feature phức tạp, dùng observation dạng vector đơn giản:

```python
shape = (3,)
[current_macro_ptr / max_macros, previous_cost, last_reward]
```

Sau khi chạy ổn mới nâng cấp graph/netlist features.

### 11.4. Reward

Reward an toàn:

```python
reward = (previous_cost - current_cost) * reward_scale
```

Nếu action lỗi:

```python
reward = invalid_action_penalty
```

Không dùng `get_congestion_cost()` làm reward chính ở version đầu.

### 11.5. Action mask

Nếu dùng `MaskablePPO`, environment nên có:

```python
def action_masks(self):
    return np.ones(self.action_space.n, dtype=bool)
```

Ban đầu cho tất cả action hợp lệ để chạy được. Sau đó nâng cấp:

```text
mask out-of-bound
mask overlap dễ phát hiện
mask cell bị blockage nếu có
```

### 11.6. Cách cập nhật placement an toàn

Không gọi API setter không chắc chắn của `plc_client_os` trước.

Cách chắc chắn:

```text
1. Copy initial/current .plc sang temp file.
2. Sửa dòng node_index tương ứng.
3. restore_placement(temp_plc).
4. get_cost().
5. Nếu tốt hơn thì lưu best temp thành best_rl.plc.
```

Cách này chậm nhưng ổn định và dễ debug.

---

## 12. Bước 6 - Cài dependency RL

Dùng virtual env riêng:

```bash
cd /home/DATN
python3 -m venv rl_env
source rl_env/bin/activate

pip install --upgrade pip
pip install numpy pandas matplotlib pyyaml gymnasium stable-baselines3 sb3-contrib
```

Không cần cài `torch` riêng nếu Stable-Baselines3 tự kéo dependency phù hợp. Nếu mạng chậm, cài từng gói một.

---

## 13. Bước 7 - Train MaskablePPO

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/train_maskable_ppo.py
```

Skeleton:

```python
import argparse
from pathlib import Path
from sb3_contrib import MaskablePPO
from macro_env import MacroPlacementEnv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist", required=True)
    parser.add_argument("--init_plc", required=True)
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--max_macros", type=int, default=20)
    args = parser.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    env = MacroPlacementEnv(
        netlist=args.netlist,
        init_plc=args.init_plc,
        out_dir=args.out_dir,
        max_macros=args.max_macros,
    )

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        n_steps=256,
        batch_size=64,
        gamma=0.99,
        learning_rate=3e-4,
    )

    model.learn(total_timesteps=args.steps)
    model.save(str(Path(args.out_dir) / "maskable_ppo_model"))


if __name__ == "__main__":
    main()
```

Chạy:

```bash
cd /home/DATN/rl_macroplacement_agent/scripts
source /home/DATN/rl_env/bin/activate
export PYTHONPATH=/home/DATN/MacroPlacement/CodeElements/Plc_client:/home/DATN/rl_macroplacement_agent/scripts:$PYTHONPATH

python3 train_maskable_ppo.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45 \
  --steps 20000 \
  --max_macros 20
```

Output mong muốn:

```text
results/ppo/ariane133_ng45/maskable_ppo_model.zip
results/ppo/ariane133_ng45/reward_history.csv
results/ppo/ariane133_ng45/best_rl.plc
results/ppo/ariane133_ng45/best_proxy.json
```

---

## 14. Bước 8 - Evaluate policy và lưu best placement

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/evaluate_policy.py
```

Yêu cầu:

```text
Load model.
Run N episodes.
Lưu episode reward.
Lưu best_rl.plc.
Gọi eval_proxy.py để tạo best_proxy.json.
```

Chạy:

```bash
python3 evaluate_policy.py \
  --model /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45/maskable_ppo_model.zip \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45/eval \
  --episodes 10
```

---

## 15. Bước 9 - Plot training curve

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/plot_training.py
```

Input:

```text
reward_history.csv
```

Output:

```text
results/figures/ariane133_ng45_reward_curve.png
```

Mục tiêu báo cáo:

```text
Có đồ thị reward/cost theo episode hoặc timestep.
Không cần reward phải tốt ngay; cần chứng minh loop học chạy được.
```

---

## 16. Bước 10 - Convert `.plc` sang OpenROAD Tcl

Có script của MacroPlacement:

```bash
/home/DATN/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py
```

Mục tiêu:

```text
best_rl.plc + netlist.pb.txt -> macro placement Tcl
```

Chạy thử:

```bash
python3 /home/DATN/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py \
  /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45/best_rl.plc \
  /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  /home/DATN/rl_macroplacement_agent/results/openroad/ariane133_ng45/best_rl_macro_place_raw.tcl
```

Sau đó kiểm tra file Tcl:

```bash
head -50 /home/DATN/rl_macroplacement_agent/results/openroad/ariane133_ng45/best_rl_macro_place_raw.tcl
```

Nếu command dạng `placeInstance`, cần convert sang OpenROAD command phù hợp.

OpenROAD thường dùng dạng:

```tcl
place_cell -inst_name <inst> -origin {<x> <y>} -orient R0 -status FIRM
```

Script chuyển đổi:

```bash
/home/DATN/rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py
```

Nhiệm vụ:

```text
Đọc Tcl raw.
Nếu thấy placeInstance, chuyển sang place_cell.
Nếu đã đúng OpenROAD Tcl, giữ nguyên hoặc chỉ normalize.
```

---

## 17. Bước 11 - Đưa placement vào OpenROAD

### 17.1. Cách mục tiêu

OpenROAD-flow-scripts có thể dùng macro placement Tcl nếu design config/flow hỗ trợ biến tương ứng. Cần kiểm tra file local:

```bash
grep -R "MACRO_PLACEMENT" -n /home/DATN/OpenROAD-flow-scripts/flow/scripts /home/DATN/OpenROAD-flow-scripts/flow/designs | head -50
```

Tìm các biến kiểu:

```text
MACRO_PLACEMENT_TCL
MACRO_PLACEMENT
PLACE_PINS_ARGS
RTLMP_FLOW
```

Nếu có `MACRO_PLACEMENT_TCL`, export:

```bash
export MACRO_PLACEMENT_TCL=/home/DATN/rl_macroplacement_agent/results/openroad/ariane133_ng45/best_rl_macro_place_openroad.tcl
```

Sau đó chạy ORFS với design config đúng của testcase macro.

### 17.2. Nếu chưa có design config macro trong ORFS

Không ép `gcd` vì `gcd` không có macro. Cần dùng testcase có macro từ MacroPlacement flow, ví dụ `ariane133`/NanGate45.

Tìm OpenROAD scripts trong MacroPlacement:

```bash
find /home/DATN/MacroPlacement/Flows/NanGate45/ariane133 -maxdepth 5 -type f | grep -i OpenROAD | head -100
find /home/DATN/MacroPlacement/Flows/NanGate45/ariane133 -maxdepth 5 -type f | grep -E "config.mk|\.tcl$|\.def$|\.lef$|\.lib$" | head -100
```

Agent phải xác định design config thật trước khi chạy.

### 17.3. Chạy OpenROAD evaluation

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/run_openroad_eval.sh
```

Skeleton:

```bash
#!/usr/bin/env bash
set -euo pipefail

DESIGN_CONFIG="$1"
MACRO_TCL="$2"
OUT_DIR="$3"

mkdir -p "$OUT_DIR"

cd /home/DATN/OpenROAD-flow-scripts/flow

export MACRO_PLACEMENT_TCL="$MACRO_TCL"

env -u DISPLAY QT_QPA_PLATFORM=offscreen \
  make DESIGN_CONFIG="$DESIGN_CONFIG" \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  -j1 2>&1 | tee "$OUT_DIR/openroad.log"
```

Nếu full route quá khó ở lần đầu, mục tiêu tối thiểu:

```text
OpenROAD đọc được macro Tcl.
Flow đi qua floorplan/place.
Có report hoặc checkpoint.
```

---

## 18. Bước 12 - So sánh kết quả

Script:

```bash
/home/DATN/rl_macroplacement_agent/scripts/compare_results.py
```

Bảng cần tạo:

| Method | Proxy cost | Wirelength | Density | Congestion | OpenROAD route | WNS/TNS | Runtime | Ghi chú |
|---|---:|---:|---:|---:|---|---:|---:|---|
| Initial | ... | ... | ... | optional | ... | ... | ... | baseline |
| Legalized | ... | ... | ... | optional | ... | ... | ... | provided placement |
| RL-PPO | ... | ... | ... | optional | ... | ... | ... | model train |
| OpenROAD macro placer | ... | ... | ... | optional | ... | ... | ... | EDA baseline |

Output:

```text
results/compare_summary.csv
results/compare_summary.md
results/figures/cost_comparison.png
```

---

## 19. Các vấn đề kỹ thuật và cách xử lý

### 19.1. `plc_wrapper_main` bị AccessDenied

Không fix bằng cách tải lại vô hạn. Ghi nhận:

```text
Google placement cost binary không public trong môi trường hiện tại.
Dùng plc_client_os làm fallback open-source.
```

### 19.2. `get_congestion_cost()` lỗi

Không để crash pipeline. Dùng:

```python
try:
    congestion = plc.get_congestion_cost()
except Exception as e:
    congestion_error = repr(e)
```

Báo cáo:

```text
Congestion proxy trong fallback open-source chưa ổn định với mọi testcase.
Milestone dùng get_cost/wirelength proxy để chứng minh RL loop.
OpenROAD được dùng ở milestone 4 để kiểm chứng vật lý.
```

### 19.3. `.plc` coordinate khác OpenROAD coordinate

Trong `.plc`, nhiều flow dùng tọa độ tâm macro. OpenROAD Tcl thường đặt origin/lower-left. Khi convert cần kiểm tra:

```text
x_origin = x_center - macro_width / 2
y_origin = y_center - macro_height / 2
```

Không được bỏ qua width/height.

### 19.4. RL học không cải thiện ngay

Không coi là fail nếu lần đầu PPO chưa tốt hơn `legalized.plc`. Cần ghi:

```text
Mục tiêu milestone là triển khai loop RL chạy được.
QoR tối ưu là mục tiêu nghiên cứu tiếp theo.
```

### 19.5. Action space quá lớn

Giải pháp:

```text
Dùng max_macros nhỏ trước, ví dụ 20.
Dùng grid gốc của .plc.
Dùng MaskablePPO.
Sau đó tăng dần macro count.
```

### 19.6. OpenROAD flow không khớp testcase

Không ép chạy `gcd` cho macroplacement. Cần tìm đúng scripts/configs trong:

```bash
/home/DATN/MacroPlacement/Flows/NanGate45/ariane133
```

Nếu chưa đưa được vào ORFS đầy đủ, tạo milestone trung gian:

```text
.plc -> Tcl conversion success
Tcl syntax checked
OpenROAD source Tcl không lỗi trên minimal design context
```

---

## 20. Deliverables agent phải tạo

### 20.1. Code deliverables

```text
rl_macroplacement_agent/configs/ariane133_ng45.yaml
rl_macroplacement_agent/scripts/eval_proxy.py
rl_macroplacement_agent/scripts/inspect_dataset.py
rl_macroplacement_agent/scripts/plc_utils.py
rl_macroplacement_agent/scripts/macro_env.py
rl_macroplacement_agent/scripts/train_maskable_ppo.py
rl_macroplacement_agent/scripts/evaluate_policy.py
rl_macroplacement_agent/scripts/plot_training.py
rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py
rl_macroplacement_agent/scripts/run_openroad_eval.sh
rl_macroplacement_agent/scripts/compare_results.py
```

### 20.2. Result deliverables

```text
rl_macroplacement_agent/results/proxy/ariane133_ng45/initial.json
rl_macroplacement_agent/results/proxy/ariane133_ng45/legalized.json
rl_macroplacement_agent/results/ppo/ariane133_ng45/reward_history.csv
rl_macroplacement_agent/results/ppo/ariane133_ng45/best_rl.plc
rl_macroplacement_agent/results/ppo/ariane133_ng45/best_proxy.json
rl_macroplacement_agent/results/figures/ariane133_ng45_reward_curve.png
rl_macroplacement_agent/results/openroad/ariane133_ng45/best_rl_macro_place_openroad.tcl
rl_macroplacement_agent/results/compare_summary.md
```

### 20.3. Report deliverables

```text
rl_macroplacement_agent/docs/MILESTONE_3_RL_IMPLEMENTATION_REPORT.md
rl_macroplacement_agent/docs/MILESTONE_4_OPENROAD_INTEGRATION_PLAN.md
```

---

## 21. Nội dung báo cáo milestone 3 nên viết

Dùng đoạn sau làm khung:

```markdown
# Milestone 3 - Chạy baseline placement và RL loop

## Mục tiêu
Triển khai một vòng lặp placement/học tăng cường trên benchmark có macro thật bằng dữ liệu chuẩn từ MacroPlacement.

## Dữ liệu đầu vào
- `netlist.pb.txt`: biểu diễn graph/netlist cho circuit-training-style placement.
- `initial.plc`: placement ban đầu, dùng làm reset state.
- `legalized.plc`: baseline placement tham chiếu.

## Công cụ
- MacroPlacement `plc_client_os` / `PlacementCost` để tính proxy cost.
- Stable-Baselines3 / sb3-contrib để chạy PPO/MaskablePPO.
- VisualPlacement để quan sát layout.

## Kết quả
- Proxy cost cho initial/legalized.
- RL loop chạy được.
- Reward history được lưu.
- Placement tốt nhất được lưu thành `best_rl.plc`.

## Giới hạn
- Không sử dụng được `plc_wrapper_main` do binary không public trong môi trường hiện tại.
- Congestion proxy trong fallback có thể không ổn định, nên reward chính dùng `get_cost`.
```

---

## 22. Nội dung báo cáo milestone 4 nên viết

```markdown
# Milestone 4 - Đưa placement quay lại OpenROAD

## Mục tiêu
Kiểm chứng placement sinh bởi RL không chỉ tốt theo proxy cost mà còn có thể đưa vào flow EDA open-source để đánh giá vật lý.

## Quy trình
1. Lấy `best_rl.plc` từ milestone 3.
2. Convert sang OpenROAD macro placement Tcl.
3. Nạp vào OpenROAD/OpenROAD-flow-scripts.
4. Chạy placement/refine/route nếu môi trường cho phép.
5. Trích xuất report và đối chiếu với proxy cost.

## Chỉ số so sánh
- Proxy cost.
- Wirelength.
- Density/congestion nếu có.
- Route success.
- Timing slack nếu có.
- Runtime.

## Kết luận mong muốn
Flow open-source có thể tạo pipeline nghiên cứu tương tự AlphaChip ở mức thực nghiệm, nhưng chưa tương đương hệ thống Google full do thiếu cost engine chính thức và backend công nghiệp.
```

---

## 23. Commit checklist

Sau khi tạo code và kết quả:

```bash
cd /home/DATN

git status

git add rl_macroplacement_agent Quy_trinh

git commit -m "Add open-source RL macroplacement flow specification and initial implementation"

git push
```

Nếu repo lớn, không commit model nặng:

```bash
find rl_macroplacement_agent/results -type f -size +50M
```

Thêm vào `.gitignore` nếu cần:

```text
*.zip
*.pt
*.pth
*.pkl
rl_macroplacement_agent/results/ppo/**/maskable_ppo_model.zip
```

---

## 24. Thứ tự triển khai ưu tiên cho Codex agent

Làm đúng thứ tự sau:

```text
1. Tạo thư mục rl_macroplacement_agent.
2. Tạo config ariane133_ng45.yaml.
3. Viết inspect_dataset.py.
4. Viết eval_proxy.py.
5. Chạy eval_proxy cho initial/legalized.
6. Viết plc_utils.py đọc/ghi .plc.
7. Viết macro_env.py tối giản.
8. Viết train_maskable_ppo.py.
9. Train 1 run ngắn 1k timesteps để smoke test.
10. Nếu smoke test OK, train 20k timesteps.
11. Lưu best_rl.plc và reward_history.csv.
12. Plot reward curve.
13. Convert best_rl.plc sang OpenROAD Tcl.
14. Tìm ORFS/MacroPlacement OpenROAD config tương ứng ariane133.
15. Thử OpenROAD evaluation.
16. Tạo compare_summary.md.
17. Cập nhật báo cáo milestone.
```

---

## 25. Định nghĩa thành công

### Thành công mức 1 - đủ Milestone 3

```text
initial.json và legalized.json có cost.
RL loop chạy được ít nhất 1k timesteps.
Có reward_history.csv.
Có best_rl.plc.
Có báo cáo giải thích hạn chế plc_wrapper_main.
```

### Thành công mức 2 - tốt cho báo cáo

```text
Train 20k timesteps.
Có reward curve.
Có so sánh initial/legalized/RL.
Có visual placement.
```

### Thành công mức 3 - nối được Milestone 4

```text
best_rl.plc convert được sang OpenROAD Tcl.
OpenROAD đọc placement Tcl.
Có report vật lý hoặc checkpoint sau placement.
```

### Thành công mức 4 - nghiên cứu tốt

```text
OpenROAD route được.
Có so sánh proxy cost vs physical QoR.
Có phân tích tại sao proxy không luôn tương quan với route/timing.
```

---

## 26. Câu chốt để nhớ

```text
MacroPlacement = data + translators + proxy cost + baseline tools.
Circuit Training = AlphaChip-style RL framework nhưng phụ thuộc cost binary.
plc_wrapper_main = không public trong môi trường hiện tại.
Open-source replacement = plc_client_os + PPO/MaskablePPO + OpenROAD verification.
```

Flow đúng cho DATN:

```text
Không cố tái tạo AlphaChip full.
Hãy tạo AlphaChip-like open-source research flow.
```

---

## 27. Nguồn tham khảo kỹ thuật nên đọc

Agent nên đọc các file/tài liệu sau trong repo local:

```bash
/home/DATN/Quy_trinh/MILESTONE_1.md
/home/DATN/Quy_trinh/MILESTONE_2.md
/home/DATN/Quy_trinh/MILESTONE_3.md
/home/DATN/Quy_trinh/MILESTONE_4.md

/home/DATN/MacroPlacement/README.md
/home/DATN/MacroPlacement/CodeElements/Plc_client/plc_client_os.py
/home/DATN/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py

/home/DATN/circuit_training/README.md
/home/DATN/circuit_training/docs/NETLIST_FORMAT.md
/home/DATN/circuit_training/docs/PLACEMENT_COST.md

/home/DATN/OpenROAD-flow-scripts/flow/scripts
```

Tài liệu public cần đối chiếu khi cần:

```text
MacroPlacement README / Flows / ProxyCost docs
Google Circuit Training README
OpenROAD macro placement docs
Stable-Baselines3 PPO docs
sb3-contrib MaskablePPO docs
```
