# DATN: Ứng dụng học tăng cường cho macro placement trong thiết kế vi mạch

Dự án này nghiên cứu cách áp dụng **Reinforcement Learning (RL)** vào bài toán **macro placement** trong quy trình thiết kế vi mạch số, theo hướng gần với **AlphaChip / Circuit Training**, nhưng sử dụng một stack open-source có thể chạy lại được:

```text
MacroPlacement benchmark
    -> graph/netlist + placement data
    -> RL environment
    -> macro-placement policy
    -> .plc placement result
    -> OpenROAD / physical-design evaluation
```

Repo hiện chứa hai nhánh thực nghiệm:

1. **Baseline đơn giản**: `MaskablePPO + MLP`, dùng để xác nhận pipeline RL chạy end-to-end.
2. **Hướng nghiên cứu chính**: agent **AlphaChip-like graph-based**, dùng graph observation, sparse connectivity, current macro, action mask và actor-critic policy gần hơn với tinh thần Circuit Training.

Các kết quả nghiên cứu, công thức, lỗi đã sửa, bảng thực nghiệm và kết luận hiện tại được lưu trong:

```text
RESULTS.md
```

## 1. Vì sao RL phù hợp với thiết kế vi mạch?

Trong physical design, nhiều bài toán có:

- không gian tìm kiếm rất lớn,
- nhiều ràng buộc hình học và routing,
- chi phí đánh giá nghiệm cao,
- quyết định ban đầu ảnh hưởng mạnh đến chất lượng cuối cùng.

Macro placement là một ví dụ điển hình. Với hàng chục đến hàng trăm macro, số cấu hình vị trí là rất lớn; một placement kém có thể làm tăng wirelength, gây nghẽn routing, làm xấu timing và giảm chất lượng toàn chip. RL phù hợp ở đây vì agent có thể học chính sách quyết định tuần tự:

```text
quan sát trạng thái hiện tại -> chọn vị trí macro tiếp theo -> nhận phản hồi chất lượng placement
```

Thay vì chỉ tối ưu một nghiệm đơn lẻ, agent học một **policy** có thể tái sử dụng trên nhiều episode hoặc nhiều mức độ khó khác nhau.

## 2. Cơ sở lý thuyết ngắn gọn

### 2.1 Reinforcement Learning

Một bài toán RL thường được mô tả như một **Markov Decision Process (MDP)**:

$$
\mathcal{M} = (\mathcal{S}, \mathcal{A}, P, R, \gamma)
$$

trong đó:

- \(\mathcal{S}\): tập trạng thái,
- \(\mathcal{A}\): tập hành động,
- \(P\): động lực chuyển trạng thái,
- \(R\): hàm thưởng,
- \(\gamma\): hệ số chiết khấu.

Trong macro placement:

| Thành phần RL | Ý nghĩa trong bài toán |
|---|---|
| State / Observation | netlist graph, metadata, macro hiện tại, node features, action mask |
| Action | chọn grid cell hợp lệ để đặt macro hiện tại |
| Reward | phản hồi dựa trên proxy cost / wirelength / density / congestion |
| Episode | một lần đặt xong chuỗi macro cần xét |
| Policy | chiến lược chọn vị trí macro theo trạng thái |

### 2.2 Reward trong flow hiện tại

Baseline MLP dùng reward theo cải thiện từng bước:

$$
r_t = \alpha \left(C_{t-1} - C_t\right)
$$

Nhánh AlphaChip-like hiện dùng terminal reward sau khi hoàn tất episode:

$$
R = \alpha \left(C_{\mathrm{init}} - C_{\mathrm{final}}\right)
$$

với \(C\) là proxy placement cost và \(\alpha\) là hệ số scale reward.

### 2.3 PPO

Agent AlphaChip-like dùng PPO. Hàm mục tiêu policy dạng clipped:

$$
\mathcal{L}_{\mathrm{policy}}
=
-\mathbb{E}_t
\left[
\min
\left(
\rho_t A_t,
\operatorname{clip}(\rho_t, 1-\epsilon, 1+\epsilon) A_t
\right)
\right]
$$

trong đó:

$$
\rho_t = \frac{\pi_{\theta}(a_t \mid s_t)}{\pi_{\theta_{\mathrm{old}}}(a_t \mid s_t)}
$$

Ước lượng advantage dùng GAE:

$$
A_t = \delta_t + \gamma \lambda (1-d_t) A_{t+1}
$$

$$
\delta_t = r_t + \gamma (1-d_t)V_{\phi}(s_{t+1}) - V_{\phi}(s_t)
$$

## 3. Quy trình EDA và vị trí của macro placement

Quy trình thiết kế vi mạch số thường đi qua các pha:

```text
RTL -> Synthesis -> Floorplan -> Placement -> CTS -> Routing -> Signoff / Reports
```

| Pha | Vai trò chính | Công cụ open-source trong dự án |
|---|---|---|
| RTL / logic | mô tả hành vi thiết kế | Verilog/SystemVerilog |
| Synthesis | RTL -> gate-level netlist | Yosys |
| Floorplan | die/core, IO, macro region | OpenROAD / ORFS |
| Placement | đặt cell và macro | RL agent, OpenROAD, DREAMPlace |
| CTS | chèn clock tree | OpenROAD |
| Routing | kết nối dây vật lý | OpenROAD |
| Evaluation | wirelength, timing, congestion, power | MacroPlacement proxy + OpenROAD reports |

### Macro placement là gì?

`Macro` là các khối lớn như SRAM, memory compiler block, register file hoặc IP lớn. Macro placement quyết định:

- vị trí \((x, y)\),
- orientation,
- quan hệ hình học với các macro khác,
- ảnh hưởng đến wirelength, congestion, timing và routeability.

Trong flow này, agent RL đặt **hard macros** tuần tự trên canvas. Sau đó kết quả có thể được đưa trở lại flow EDA để đánh giá sâu hơn.

## 4. Workflow tổng thể của dự án

```text
Benchmark MacroPlacement
  -> netlist.pb.txt + initial.plc
  -> feature extraction / RL environment
  -> training policy
  -> final .plc placement
  -> proxy evaluation
  -> optional .tcl conversion
  -> OpenROAD visualization / physical evaluation
```

### 4.1 Dữ liệu vào của RL

Benchmark đầu tiên được dùng là:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

Các file chính:

| File | Dùng để làm gì |
|---|---|
| `netlist.pb.txt` | graph/netlist text-format chứa node, macro, port, feature và connectivity cho môi trường RL |
| `initial.plc` | placement metadata và trạng thái khởi tạo; khi bắt đầu episode theo kiểu Circuit Training, các movable node được unplace trước khi đặt hard macro tuần tự |
| `legalized.plc` | placement tham chiếu đã hợp thức hóa, dùng cho đối chiếu hoặc baseline |

### 4.2 Các định dạng file EDA quan trọng

| Định dạng | Ý nghĩa |
|---|---|
| `.v`, `.sv` | RTL hoặc gate-level netlist |
| `.lib` | thư viện timing / power |
| `.lef` | mô tả hình học layer, cell, macro |
| `.def` | trao đổi floorplan, placement, routing |
| `.odb` | database checkpoint nội bộ của OpenROAD |
| `.sdc` | ràng buộc timing |
| `.spef` | parasitic sau routing |
| `.pb.txt` | protobuf text netlist cho flow kiểu Circuit Training |
| `.plc` | placement canvas / lời giải placement cho RL |
| `.tcl` | script điều khiển EDA tool, ví dụ đặt macro trong OpenROAD / Innovus |

### 4.3 Chuyển kết quả RL về EDA

`MacroPlacement` có sẵn converter chính thức:

```bash
MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py
```

Nó chuyển:

```text
.plc + netlist.pb.txt -> placement Tcl dạng placeInstance
```

Nếu cần mở trong OpenROAD, repo có adapter:

```bash
rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py
```

để đổi dialect Tcl:

```text
placeInstance -> place_macro / place_inst
```

## 5. Kiến trúc code chính

```text
rl_macroplacement_agent/
├── scripts/
│   ├── macro_env.py                       # baseline environment 8 chiều
│   ├── train_maskable_ppo.py              # baseline MaskablePPO + MLP
│   ├── evaluate_policy.py                 # đánh giá baseline
│   ├── alphachip_like_features.py         # graph observation extractor
│   ├── alphachip_like_model.py            # graph actor-critic model
│   ├── alphachip_like_agent.py            # PPO utilities
│   ├── train_alphachip_like_ppo.py        # trainer AlphaChip-like
│   ├── evaluate_alphachip_like_policy.py  # evaluator AlphaChip-like
│   ├── eval_proxy.py                      # proxy-cost evaluator
│   ├── plc_to_openroad_tcl.py             # adapter Tcl cho OpenROAD
│   └── install_dreamplace.sh              # build DREAMPlace + patch CUDA 12
└── requirements.txt
```

## 6. Cài đặt môi trường

### 6.1 System dependencies

```bash
cd /home/DATN
bash rl_macroplacement_agent/scripts/install_system_deps_ubuntu.sh
```

Script này cài các package nền như:

- `build-essential`, `cmake`, `bison`, `flex`
- `libboost-all-dev`, `libeigen3-dev`
- `tcl`, `tcl-dev`
- `python3-dev`, `python3-pip`, `python3-venv`
- `libcairo2`, `zlib1g-dev`

### 6.2 Python environment

Nếu chưa có virtual environment:

```bash
cd /home/DATN
python3 -m venv rl_env
source rl_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r rl_macroplacement_agent/requirements.txt
```

### 6.3 Build DREAMPlace

DREAMPlace là baseline placement gradient-based và cũng là một thành phần tham chiếu hữu ích trong dự án.

```bash
cd /home/DATN
source rl_env/bin/activate
bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Script này sẽ:

1. clone DREAMPlace nếu chưa có,
2. cập nhật submodule,
3. cài dependency Python cần thiết,
4. phát hiện CUDA nếu có,
5. áp dụng patch tương thích CUDA 12.x / CUB nếu cần,
6. build và install DREAMPlace.

Smoke test tùy chọn:

```bash
RUN_SMOKE_TEST=1 bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

### 6.4 OpenROAD / OpenROAD-flow-scripts

Dự án dùng OpenROAD để kiểm tra physical-design flow và để xem lại placement. Tài liệu chi tiết hơn nằm trong:

```text
BUILD_GUIDE.md
FULL_OPEN_SOURCE_RTL_TO_RL_GUIDE.md
```

Một flow sanity-check với ORFS có thể chạy theo kiểu:

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  synth floorplan place -j1
```

## 7. Chạy học tăng cường

README này chỉ mô tả cách **áp dụng và chạy RL workflow cơ bản**, không liệt kê các lệnh curriculum research batch.

### 7.1 Kiểm tra graph observation của agent AlphaChip-like

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

Mục đích:

- xác nhận feature graph sinh đúng,
- xác nhận mask hợp lệ,
- xác nhận model forward pass chạy được.

### 7.2 Chạy baseline MaskablePPO

```bash
cd /home/DATN
source rl_env/bin/activate

python rl_macroplacement_agent/scripts/train_maskable_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/ppo/train \
  --steps 3000 \
  --max_macros 5

python rl_macroplacement_agent/scripts/evaluate_policy.py \
  --model rl_macroplacement_agent/results/ariane133_ng45/ppo/train/maskable_ppo_model.zip \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/ppo/eval \
  --max_macros 5 \
  --deterministic
```

### 7.3 Chạy agent AlphaChip-like

```bash
cd /home/DATN
source rl_env/bin/activate

python rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/train \
  --episodes 615 \
  --max_macros 5 \
  --seed 1

python rl_macroplacement_agent/scripts/evaluate_alphachip_like_policy.py \
  --model rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/train/alphachip_like_actor_critic.pt \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval \
  --max_macros 5 \
  --deterministic
```

Kết quả chính sinh ra gồm:

| File | Ý nghĩa |
|---|---|
| `alphachip_like_actor_critic.pt` | checkpoint model |
| `alphachip_like_training_history.csv` | lịch sử train theo episode |
| `alphachip_like_train_summary.json` | tóm tắt quá trình train |
| `alphachip_like_final.plc` | placement cuối cùng sau eval |
| `alphachip_like_eval_summary.json` | metric eval |

### 7.4 Đánh giá proxy cost

```bash
python rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final.plc \
  --out rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/proxy_metrics.json
```

### 7.5 Chuyển placement sang Tcl để xem trong OpenROAD

Dùng converter chính thức của MacroPlacement:

```bash
python MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py \
  rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final.plc \
  MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final_raw.tcl
```

Nếu muốn OpenROAD đọc trực tiếp:

```bash
python rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py \
  --in_tcl rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final_raw.tcl \
  --out_tcl rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/eval/alphachip_like_final_openroad.tcl \
  --mode place_macro \
  --escape_brackets
```

## 8. Kết quả hiện tại

Tóm tắt ngắn:

- baseline MLP cho thấy bài toán khó dần khi số macro tăng,
- nhánh AlphaChip-like đã chạy end-to-end,
- đã sửa hai lỗi quan trọng:
  1. normalize advantage sai mức,
  2. reset môi trường chưa đúng kiểu Circuit Training,
- khi train đủ budget, curriculum theo số macro đã cho tín hiệu tốt hơn scratch ở bài 20 macro trên nhiều seed.

Chi tiết đầy đủ nằm trong:

```text
RESULTS.md
PROGRESS.md
```

## 9. Giới hạn hiện tại và hướng phát triển

Hiện tại dự án chủ yếu đánh giá bằng **proxy metrics**. Để hoàn tất nghiên cứu theo hướng gần `MacroPlacement`, các bước tiếp theo cần có:

1. mở rộng số macro lên bài toán khó hơn,
2. lặp nhiều seed và báo cáo `mean ± std`,
3. đưa placement RL trở lại OpenROAD / P&R flow,
4. trích các metric vật lý như:
   - routed wirelength,
   - power,
   - WNS,
   - TNS,
   - congestion,
5. lập bảng so sánh với các baseline vật lý theo phong cách `MacroPlacement`.

## 10. Tài liệu liên quan trong repo

| File | Nội dung |
|---|---|
| `RESULTS.md` | kết quả nghiên cứu hiện tại, công thức, bảng số liệu, kết luận |
| `PROGRESS.md` | nhật ký tiến độ theo ngày |
| `BUILD_GUIDE.md` | hướng dẫn build / setup chi tiết |
| `FULL_OPEN_SOURCE_RTL_TO_RL_GUIDE.md` | mô tả đầy đủ flow RTL -> RL -> EDA |
| `AGENT_RL_MACROPLACEMENT_OPEN_SOURCE_FLOW.md` | đặc tả kỹ thuật và nguyên tắc triển khai cho agent |
| `rl_macroplacement_agent/README.md` | README chuyên cho pipeline PPO / DREAMPlace |

---

Dự án này hướng tới một câu hỏi trung tâm:

> Liệu một agent học tăng cường có thể học được chính sách macro placement hữu ích trong một flow open-source, và kết quả đó có còn giữ được lợi ích khi đưa trở lại quy trình EDA thực tế hay không?
