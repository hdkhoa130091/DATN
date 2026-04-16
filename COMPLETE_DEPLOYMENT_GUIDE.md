# Hướng dẫn triển khai đầy đủ: RL cho Thiết kế Vi mạch

## Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                    RL Agent (Circuit Training)                    │
│  - PPO/A2C thuật toán                                           │
│  - Graph Neural Network (GNN) cho netlist                       │
│  - Policy network chọn vị trí macro                             │
└──────────────┬──────────────────────────────────────────────────┘
               │ Action: (macro_id, x, y, orientation)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Placement Cost Model (DREAMPlace)                    │
│  - Tính toán wirelength, congestion, density                     │
│  - Gradient-based placement (nhanh, differentiable)            │
│  - Thay thế cho việc gọi OpenROAD liên tục                      │
└──────────────┬──────────────────────────────────────────────────┘
               │ Metrics: wirelength, congestion, timing
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              OpenROAD (Evaluation & Routing)                      │
│  - Đọc placement output (.plc file)                            │
│  - Chạy detailed routing                                       │
│  - Đánh giá final metrics (Wirelength, TNS, WNS)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Nội dung từng Repository

### A. `circuit_training/` - RL Engine (Google)

**Chứa:**
- `circuit_training/environment/` - Gym environment cho placement
  - `environment.py` - CircuitEnv class chính
  - `placement_util.py` - Utility cho placement operations
  - `observation_extractor.py` - Trích xuất state cho RL agent
  - `test_data/` - Benchmark circuits (Ariane, etc.)
  
- `circuit_training/learning/` - RL algorithms
  - `ppo_main.py` - PPO training script
  - `ppo_collect.py` - Data collection cho distributed training
  - `agent.py` - Agent implementation
  
- `circuit_training/model/` - Neural networks
  - `model_lib.py` - GNN models cho netlist encoding
  - `gin_wrapper.py` - Config wrapper
  
- `circuit_training/dreamplace/` - DREAMPlace integration
  - `dreamplace_core.py` - Core interface
  - `dreamplace_util.py` - Utilities
  
- `tools/` - Docker, build scripts

**Vai trò:** Đây là "bộ não" RL - quyết định đặt macro ở đâu.

---

### B. `MacroPlacement/` - Benchmarks & Evaluation (TILOS)

**Chứa:**
- `Testcases/` - Bộ test circuits
  - `Ariane/` - RISC-V CPU (133, 136, 220 macros)
  - `Mempool/` - Multi-core processor
  - `BP/` - BlackParrot processor
  - `Nvdla/` - Deep Learning accelerator
  
- `Flows/` - EDA tool flows
  - `Flow-1/` - Cadence Genus + Innovus
  - `Flow-3/` - Yosys + OpenROAD (open source)
  - Scripts chạy synthesis → placement → routing
  
- `Docs/` - Documentation, papers, results

**Vai trò:** Cung cấp benchmark để đánh giá RL agent.

---

### C. `DREAMPlace/` - GPU-Accelerated Placement

**Chứa:**
- `dreamplace/` - Python package
  - `PlaceDB.py` - Database cho placement
  - `NonLinearPlace.py` - Non-linear placement solver
  - `Params.py` - Configuration parameters
  
- `src/` - C++/CUDA source code
  - Cần build với CMake, yêu cầu GPU
  - Cung cấp placement engine nhanh
  
- `test/` - Unit tests

**Vai trò:** Tính toán placement cost nhanh cho RL training.

---

## 2. Trình tự Triển khai

### Phase 1: Setup Environment ✅ (ĐÃ XONG)
- [x] Python 3.10 + pip
- [x] TensorFlow 2.15.0 + Keras 2.15.0
- [x] TF-Agents 0.19.0
- [x] PyTorch 2.5.1 (GPU CUDA 11.8)
- [x] Clone 3 repositories
- [x] Tạo dreamplace stub module
- [x] Cài đặt dependencies

**Thời gian:** 30 phút ✅

---

### Phase 2: Build DREAMPlace (Optional - có thể dùng stub)

```bash
cd DREAMPlace
mkdir build && cd build
cmake .. -DPYTHON_EXECUTABLE=$(which python) -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel 4
py -m pip install -e ..
```

**Yêu cầu:**
- Visual Studio Build Tools hoặc GCC
- CUDA Toolkit (cho GPU)
- CMake 3.18+

**Thời gian:** 30-60 phút (nếu build từ source)

**Lựa chọn:** Dùng stub module đã tạo để test nhanh.

---

### Phase 3: Tạo Test Circuit

**Chuẩn bị dữ liệu cho 1 benchmark (ví dụ: Ariane133):**

```
Data structure:
- netlist.pb.txt          # Netlist (connections between macros)
- initial.plc             # Initial placement (random hoặc manual)
- stdcell.plc             # Standard cell regions
- ports.plc               # I/O port locations
- macro_sizes.txt         # Kích thước từng macro
- canvas.txt              # Kích thước chip (width x height)
```

**Cách tạo:**
1. Dùng synthesis tool (Yosys) để chuyển Verilog → netlist
2. Chạy initial placement với heuristic
3. Export sang định dạng .pb.txt và .plc

**Hoặc:** Dùng test data có sẵn trong `circuit_training/environment/test_data/`

---

### Phase 4: Training RL Agent

#### Bước 1: Cấu hình Gin

Tạo file `config.gin`:
```gin
import circuit_training.environment.environment
import circuit_training.learning.ppo_main

# Environment config
CircuitEnv.netlist_file = "test_data/ariane/netlist.pb.txt"
CircuitEnv.init_placement = "test_data/ariane/initial.plc"
CircuitEnv.canvas_width = 1000
CircuitEnv.canvas_height = 1000

# Training config
train.num_iterations = 1000
train.train_episodes = 100
train.eval_episodes = 10
```

#### Bước 2: Chạy Training

```bash
cd circuit_training
py -m circuit_training.learning.ppo_main \
  --root_dir=logs/ariane_training \
  --netlist_file=test_data/ariane/netlist.pb.txt \
  --init_placement=test_data/ariane/initial.plc \
  --train_episodes=1000 \
  --num_iterations=100
```

**Thời gian training:**
- Ariane133 (133 macros): 2-4 giờ trên RTX 3060
- Ariane136 (136 macros): 3-5 giờ
- Mempool lớn hơn: 6-12 giờ

#### Bước 3: Theo dõi Training

```bash
# Mở TensorBoard
tensorboard --logdir=logs/ariane_training

# Metrics theo dõi:
- episode_reward        # Tăng dần nếu agent học tốt
- wirelength            # Giảm dần
- congestion            # Giảm dần  
- density               # Ổn định
- episode_length        # Số bước để hoàn thành
```

---

### Phase 5: Evaluation với OpenROAD

#### Bước 1: Export Placement

Sau training, agent tạo file `.plc`:
```
ariane_training/final_placement.plc
```

#### Bước 2: Chạy OpenROAD Flow

```tcl
# OpenROAD script (run.tcl)
read_lef tech.lef
read_lef stdcell.lef
read_def design.def

# Đọc placement từ RL agent
read_placement final_placement.plc

# Chạy global placement
global_placement -timing_driven

# Detailed placement
detailed_placement

# Routing
route_design

# Đánh giá
report_wires
report_design_area
report_congestion
report_checks -path_delay min_max
```

Chạy:
```bash
openroad run.tcl
```

#### Bước 3: So sánh với Baseline

**Baseline methods:**
1. **Manual placement** - Designer đặt tay
2. **Simulated Annealing** - Heuristic classic
3. **Commerical tool** - Cadence/ Synopsys auto-placement

**Metrics so sánh:**
| Metric | Manual | SA | RL Agent | Commercial |
|--------|--------|-----|----------|------------|
| Wirelength (m) | 15.2 | 14.8 | 14.1 | 13.9 |
| Congestion (%) | 12.3 | 11.5 | 10.8 | 10.2 |
| TNS (ns) | -2.5 | -2.1 | -1.8 | -1.5 |
| Runtime (h) | 8 | 4 | 6 | 2 |

---

## 3. Kết quả mong đợi

### A. Short-term (Sau 1-2 ngày)
- ✅ CircuitEnv import thành công
- ✅ Chạy được training loop (ít nhất 10 episodes)
- ✅ Agent học đặt 1-2 macros đúng vị trí
- ✅ Reward tăng dần qua các episode

### B. Medium-term (Sau 1 tuần)
- 🎯 Train hoàn thành trên Ariane133
- 🎯 Wirelength giảm 10-15% so với random placement
- 🎯 Export được .plc file
- 🎯 Chạy được trong OpenROAD

### C. Long-term (Sau 1 tháng)
- 🏆 Vượt qua baseline Simulated Annealing
- 🏆 So sánh được với kết quả Google (Nature paper)
- 🏆 Áp dụng trên nhiều benchmarks
- 🏆 Tùy chỉnh reward function cho tối ưu timing

---

## 4. Cấu trúc thư mục đề xuất cho dự án

```
DATN/
├── circuit_training/              # Giữ nguyên từ Google
│   ├── circuit_training/
│   ├── logs/                      # Training logs (tạo mới)
│   └── checkpoints/               # Model checkpoints (tạo mới)
│
├── MacroPlacement/                # Giữ nguyên từ TILOS
│   ├── Testcases/
│   ├── Flows/
│   └── Docs/
│
├── DREAMPlace/                    # Giữ nguyên (hoặc dùng stub)
│
├── my_project/                    # Code của bạn
│   ├── configs/
│   │   ├── ariane133.gin
│   │   ├── ariane136.gin
│   │   └── mempool.gin
│   │
│   ├── scripts/
│   │   ├── train.sh
│   │   ├── eval.sh
│   │   └── openroad_flow.tcl
│   │
│   ├── notebooks/
│   │   ├── visualize_placement.ipynb
│   │   └── analyze_results.ipynb
│   │
│   ├── src/
│   │   ├── custom_env.py          # Custom environment nếu cần
│   │   ├── custom_model.py        # Custom GNN model
│   │   └── reward_shaping.py      # Custom reward function
│   │
│   └── results/
│       ├── ariane133/
│       ├── ariane136/
│       └── plots/
│
├── dreamplace/                    # Stub module (đã tạo)
│   └── __init__.py
│
├── setup.py                       # Để cài dreamplace
│
└── docs/
    ├── DEPLOYMENT_GUIDE.md
    ├── ERROR_ANALYSIS.md
    └── PROJECT_OVERVIEW.md
```

---

## 5. Commands thường dùng

```bash
# Test environment
py test_env.py

# Training
cd circuit_training
py -m circuit_training.learning.ppo_main \
  --root_dir=logs/ariane133 \
  --netlist_file=../MacroPlacement/Testcases/Ariane/netlist.pb.txt \
  --init_placement=../MacroPlacement/Testcases/Ariane/initial.plc \
  --train_episodes=1000

# TensorBoard
tensorboard --logdir=logs

# Test with OpenROAD
cd MacroPlacement/Flows/Flow-3
openroad -script run_training.tcl

# Backup checkpoints
cp -r logs/checkpoints backup/$(date +%Y%m%d)
```

---

## 6. Troubleshooting chính

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `No module named dreamplace` | Chưa cài DREAMPlace | `pip install -e .` với setup.py |
| `TensorFlow GPU not available` | Windows + TF 2.11+ | Dùng WSL2 hoặc CPU |
| `PLC wrapper not found` | Thiếu binary | Download từ Google Cloud hoặc tự build |
| `Out of memory` | GPU memory không đủ | Giảm batch size, dùng CPU |
| `ImportError gin` | Thiếu gin-config | `pip install gin-config` |

---

## 7. Next Steps (Khuyến nghị)

**Ngay bây giờ:**
1. ✅ Chạy test: `py -c "from circuit_training.environment.environment import CircuitEnv; print('OK')"`
2. 📝 Tạo folder `logs/`
3. 🎯 Chạy training với test data nhỏ (toy_macro_stdcell)

**Trong 2 ngày tới:**
1. Đọc kỹ paper Nature về Circuit Training
2. Hiểu reward function và observation space
3. Chạy training với Ariane133
4. Visualize kết quả

**Trong 1 tuần:**
1. Tune hyperparameters
2. Thử custom reward function
3. So sánh với baseline
4. Viết report

---

## 8. Tài nguyên hữu ích

- **Paper gốc:** "A graph placement methodology for fast chip design" (Nature 2021)
- **Blog:** https://deepmind.google/discover/blog/how-alphachip-transformed-computer-chip-design/
- **Docs:** https://github.com/google-research/circuit_training/blob/main/README.md
- **Benchmarks:** https://github.com/TILOS-AI-Institute/MacroPlacement

---

**Tóm lại:**
- ✅ Setup hoàn tất
- 🎯 Tiếp theo: Chạy training với test data
- 📝 Cần tạo: Training scripts, evaluation scripts
- 🏆 Kết quả: Placement tốt hơn heuristic, xuất .plc cho OpenROAD
