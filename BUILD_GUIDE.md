# RL Macro Placement - Build & Run Guide

## Current Status (April 20, 2026)

**Working Solution**: Simplified RL environment with Gymnasium + Stable-Baselines3
**Partial**: DREAMPlace integration (build issues with CUDA)

---

## Quick Start

### 1. Run RL Training (Working)

```bash
cd /home/DATN
python3 rl_macro_placement_v2.py
```

**Expected Output**:
```
============================================================
RL Macro Placement - Simplified Demo
============================================================
Testing environment...
Initial observation shape: (20,)
Step 0: Reward=-10.76, HPWL=76.09, Density=1.00
Step 1: Reward=-9.45, HPWL=65.23, Density=0.00
...
Training complete!
============================================================
```

---

## Full Setup Guide

### Prerequisites

```bash
# System dependencies
apt-get update
apt-get install -y cmake flex bison libboost-all-dev tcl-dev wget swig git

# Python 3.10+
python3 --version  # Should be 3.10 or higher
```

### Step 1: Clone Repositories

```bash
cd /home/DATN

# Clone MacroPlacement
git clone https://github.com/TILOS-AI-Institute/MacroPlace MacroPlacement

# Clone circuit_training
git clone https://github.com/google-research/circuit_training.git circuit_training

# Clone DREAMPlace with submodules
git clone --recursive https://github.com/limbo018/DREAMPlace.git DREAMPlace
```

### Step 2: Install Python Dependencies

```bash
# PyTorch (CUDA version - current system has 2.11.0+cu130)
pip install torch torchvision

# Or CPU-only version (if CUDA issues):
# pip install torch==2.0.1+cpu torchvision==0.15.2+cpu --index-url https://download.pytorch.org/whl/cpu

# NumPy (compatible version)
pip install numpy==1.24.3

# RL Libraries
pip install gymnasium stable-baselines3

# Additional dependencies
pip install matplotlib scipy pyunpack patool
```

### Step 3: Download Benchmarks

```bash
cd /home/DATN/DREAMPlace/benchmarks
python3 ispd2005_2015.py
```

This downloads ISPD2005 benchmarks to `/home/DATN/DREAMPlace/benchmarks/ispd2005/`:
- adaptec1, adaptec2, adaptec3, adaptec4
- bigblue1, bigblue2, bigblue3, bigblue4

---

## DREAMPlace Build (Optional - Has Issues)

### Attempt Build

```bash
cd /home/DATN/DREAMPlace
rm -rf build install
mkdir build && cd build

# Configure
cmake .. \
  -DCMAKE_INSTALL_PREFIX=/home/DATN/DREAMPlace/install \
  -DCMAKE_CXX_ABI=0 \
  -DPYTHON_EXECUTABLE=$(which python3)

# Build (this takes 10-30 minutes)
make -j4

# Install
make install
```

### Known Build Issues

**Error**: `undefined symbol: _ZN3c106detail14torchCheckFailEPKcS2_jRKSs`

**Cause**: CUDA version incompatibility between DREAMPlace and PyTorch 2.11.0+cu130

**Workaround**: Use CPU-only simplified RL environment (`rl_macro_placement_v2.py`)

### Fix Python 3 Imports (If Build Succeeds)

```bash
cd /home/DATN/DREAMPlace/install/dreamplace

# Fix imports in all Python files
for f in *.py; do
  sed -i 's/^import Params$/from dreamplace import Params/g' "$f"
  sed -i 's/^import PlaceDB$/from dreamplace import PlaceDB/g' "$f"
  sed -i 's/^import Timer$/from dreamplace import Timer/g' "$f"
  sed -i 's/^import NonLinearPlace$/from dreamplace import NonLinearPlace/g' "$f"
done
```

---

## Project Structure

```
/home/DATN/
├── MacroPlacement/          # TILOS AI Institute placement framework
│   ├── CodeElements/
│   ├── Flows/
│   └── Testcases/
├── circuit_training/        # Google RL for chip design
│   ├── circuit_training/
│   └── tools/
├── DREAMPlace/              # Placement engine (build issues)
│   ├── benchmarks/          # ISPD2005 testcases
│   ├── build/               # Build directory
│   ├── dreamplace/          # Source code
│   ├── install/             # Installation (if build succeeds)
│   └── thirdparty/          # Submodules
├── rl_macro_placement.py    # Original DREAMPlace integration attempt
├── rl_macro_placement_v2.py # **Working** simplified RL environment
├── PROGRESS.md              # Detailed progress log
└── BUILD_GUIDE.md           # This file
```

---

## Working Components

### 1. RL Environment (`rl_macro_placement_v2.py`)

**Features**:
- Gymnasium-compatible environment
- 5-10 macros placement simulation
- HPWL (Half-Perimeter Wirelength) reward
- Density/overlap penalty
- PPO agent from stable-baselines3

**Usage**:
```python
from rl_macro_placement_v2 import SimpleMacroPlacementEnv, RLAgent

# Create environment
env = SimpleMacroPlacementEnv(num_macros=5, canvas_size=(100, 100))

# Train agent
agent = RLAgent(env)
agent.train(total_timesteps=10000)

# Evaluate
obs, info = env.reset()
action, _ = agent.predict(obs)
obs, reward, terminated, truncated, info = env.step(action)
```

### 2. ISPD2005 Benchmarks

**Location**: `/home/DATN/DREAMPlace/benchmarks/ispd2005/`

**Benchmarks**:
- `adaptec1/` - ~200k cells
- `adaptec2/` - ~250k cells
- `adaptec3/` - ~450k cells
- `adaptec4/` - ~500k cells
- `bigblue1/` - ~300k cells
- `bigblue2/` - ~500k cells
- `bigblue3/` - ~1M cells
- `bigblue4/` - ~2M cells

---

## Testing

### Test RL Environment

```bash
cd /home/DATN
python3 -c "
from rl_macro_placement_v2 import SimpleMacroPlacementEnv
env = SimpleMacroPlacementEnv()
obs, info = env.reset()
print(f'Environment created successfully')
print(f'Observation shape: {obs.shape}')
print(f'Action space: {env.action_space}')
"
```

### Test PyTorch Installation

```bash
python3 -c "
import torch
import numpy as np
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'NumPy: {np.__version__}')
"
```

---

## Troubleshooting

### Issue: ImportError for DREAMPlace

**Solution**: Use `rl_macro_placement_v2.py` instead

### Issue: CUDA Out of Memory

**Solution**: Reduce batch size or use CPU

```python
# In rl_macro_placement_v2.py, modify:
agent = RLAgent(env)
# Or use CPU-only PyTorch
```

### Issue: stable-baselines3 not found

```bash
pip install stable-baselines3 --upgrade
```

### Issue: gymnasium API errors

```bash
pip install gymnasium --upgrade
```

---

## Next Steps

1. **Fix DREAMPlace Build**:
   - Rebuild with matching CUDA version
   - Or use CPU-only PyTorch

2. **Integrate Real Placement**:
   - Load ISPD2005 benchmarks into RL environment
   - Use DREAMPlace for wirelength calculation
   - Train on actual circuit netlists

3. **Advanced RL**:
   - Try different RL algorithms (SAC, TD3)
   - Multi-objective optimization (HPWL + density + congestion)
   - Curriculum learning from small to large circuits

4. **Evaluation**:
   - Compare with traditional placement tools
   - Measure QoR (Quality of Results)
   - Runtime analysis

---

## References

- **DREAMPlace**: https://github.com/limbo018/DREAMPlace
- **Circuit Training**: https://github.com/google-research/circuit_training
- **MacroPlacement**: https://github.com/TILOS-AI-Institute/MacroPlacement
- **Stable Baselines3**: https://stable-baselines3.readthedocs.io/
- **Gymnasium**: https://gymnasium.farama.org/

---

## Contact

For issues with this setup, check:
1. `PROGRESS.md` for detailed history
2. DREAMPlace GitHub issues for build problems
3. PyTorch/CUDA compatibility matrix
