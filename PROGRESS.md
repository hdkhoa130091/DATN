# RL Macro Placement Project - Progress Summary

## 2026-05-08 - PyTorch RL AlphaChip-Like Prototype

### Goal

This update documents the current RL direction of the thesis project:

- implement an inspectable PyTorch reinforcement-learning prototype for VLSI macro placement
- make the code structure easier to explain as `model + agent + environment`
- keep the implementation inspired by Google AlphaChip / `circuit_training`
- avoid depending on unavailable Google internal infrastructure such as `plc_wrapper_main`

The project direction is now:

```text
MacroPlacement benchmark
  -> plc_client_os PlacementCost proxy evaluator
  -> Gymnasium macro-placement environment
  -> PPO / MaskablePPO smoke test
  -> PyTorch AlphaChip-like model and PPO agent prototype
  -> future integration with richer graph observations and DREAMPlace/OpenROAD
```

### Why This Was Needed

The original Google `circuit_training` code does not look like the usual
student-level PyTorch workflow:

```text
model = PolicyNetwork(...)
agent = PPO(...)
loss.backward()
optimizer.step()
```

Instead, it creates actor and value networks through TensorFlow / TF-Agents,
uses a graph-based model, distributed actors, Reverb replay buffer, and a
placement-cost backend. That makes it difficult to show the professor a compact
`model` and `agent` implementation.

To make the research contribution easier to inspect, the repository now includes
an explicit PyTorch implementation that mirrors the main AlphaChip ideas at a
prototype level.

### Code Added

Added:

- `rl_macroplacement_agent/scripts/alphachip_like_model.py`
- `rl_macroplacement_agent/scripts/alphachip_like_agent.py`

`alphachip_like_model.py` implements:

- static metadata encoder
- node feature encoder
- edge-centric graph message passing layer
- current-node attention over all node embeddings
- policy head that outputs placement-grid logits
- value head for PPO
- action-mask support

`alphachip_like_agent.py` implements:

- PPO config
- rollout batch container
- generalized advantage estimation
- clipped PPO policy loss
- value loss
- entropy regularization
- gradient clipping and optimizer update

This gives the project a clear `model` and `agent` code path that can be
presented and improved independently from Stable-Baselines3.

### Current Experiment Result

The working smoke test still uses:

```text
Gymnasium + Stable-Baselines3 + sb3-contrib MaskablePPO
```

Benchmark:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

Command:

```bash
python3 rl_macroplacement_agent/scripts/train_maskable_ppo.py \
  --netlist /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/ppo/train \
  --steps 1000 \
  --max_macros 20
```

Observed result:

```text
total_timesteps: 1024
runtime: about 3455 seconds
best_cost: 0.04972213503402197
```

Proxy comparison:

```text
initial.plc:
  cost:       0.04972213503402197
  wirelength: 3219213.998199995
  density:    0.6067348455137481

best_rl.plc:
  cost:       0.04972213503402197
  wirelength: 3219213.998199995
  density:    0.6067348455137481

legalized.plc:
  cost:       0.07356822360533051
  wirelength: 4763107.117000044
  density:    0.49881790624435346
  congestion: 0.725914889902168
```

Interpretation:

- the RL pipeline runs end-to-end
- the agent produces a trained model file and `best_rl.plc`
- the smoke test did not improve beyond `initial.plc`
- this is expected because the current environment uses a simple 8-value
  observation and only 1000 training steps
- `congestion_cost` is unstable for the initial placement, so congestion remains
  optional in this stage

Milestone status:

```text
RL smoke test: PASS
Placement quality improvement: NOT YET
```

### Weaknesses of the Current Running RL Code

The current `train_maskable_ppo.py` path is useful for proving the flow, but it
is still much weaker than AlphaChip:

- observation is too small and does not expose the full netlist graph
- policy is the default Stable-Baselines3 MLP, not a graph neural network
- macro placement order is fixed
- reward is based on step-by-step delta cost and is hard for PPO to learn
- training is slow because `PlacementCost` and action masks are expensive
- DREAMPlace is not yet integrated into the environment loop
- there is no pretraining on multiple related chip blocks

### Why AlphaChip / circuit_training Performs Better

Public `circuit_training` uses a much richer setup:

- graph observations with sparse adjacency and edge weights
- node features such as type, size, placement state, and location
- current-node attention
- policy logits over a padded 128x128 placement canvas
- terminal reward after analytical placement / stdcell placement
- PPO training with distributed actors
- optional DREAMPlace integration for mixed-size/stdcell placement
- pretraining and fine-tuning across multiple blocks

The most important difference is not just PPO. It is:

```text
rich graph observation + GCN/attention model + distributed training + pretraining
```

### Next Improvement Plan

The next phase should start only after this progress is accepted.

Planned improvements:

1. Build an AlphaChip-like observation extractor for local MacroPlacement data.
2. Replace the current 8-value observation with graph/static/dynamic features.
3. Integrate `AlphaChipLikeActorCritic` into an actual PPO training script.
4. Keep `MaskablePPO` as the baseline and compare against the custom PyTorch PPO.
5. Build DREAMPlace and use it as a baseline/refinement tool, not as a direct
   replacement for the RL agent.
6. Add imitation/pretraining from available placements such as `initial.plc`,
   `legalized.plc`, manual placements, or multiple MacroPlacement benchmarks.

### Files to Discuss With Advisor

- `rl_macroplacement_agent/scripts/macro_env.py`
- `rl_macroplacement_agent/scripts/train_maskable_ppo.py`
- `rl_macroplacement_agent/scripts/alphachip_like_model.py`
- `rl_macroplacement_agent/scripts/alphachip_like_agent.py`
- `rl_macroplacement_agent/scripts/eval_proxy.py`

## Current Milestone

The project has reached a reproducible open-source physical-design milestone:

- ORFS sample design `nangate45/gcd` runs through OpenROAD and produces:
  - `6_final.odb`
  - `6_final.def`
  - `6_final.sdc`
  - `6_final.v`
  - `6_final.spef`
- OpenROAD GUI can be used to inspect light checkpoints such as:
  - `2_floorplan.odb`
  - `3_place.odb`
  - `6_final.odb`
- KLayout-based GDS merge is not required for this milestone and is currently blocked by an older packaged `klayout 0.26.2`.

## Completed Tasks

### 1. Repository Setup
- `MacroPlacement` is present in the repo and remains the main bridge toward open-source macro-placement data generation.
- `circuit_training` is present in the repo for the later RL stage.
- `DREAMPlace` remains optional and is not needed for the current milestone.

### 2. Open-Source Toolchain Validation
- Verified a prebuilt `OpenROAD` binary works on Ubuntu 22.04.
- Verified Ubuntu-packaged `yosys` is too old for current ORFS.
- Verified `oss-cad-suite` provides a newer `yosys` suitable for ORFS.

### 3. ORFS Flow Validation
- Successfully ran `synth`
- Successfully ran `floorplan`
- Successfully ran `place`
- Successfully ran `cts`
- Successfully ran `global_route`
- Successfully ran `detail_route`
- Successfully generated final OpenROAD artifacts before GDS merge

### 4. RL Environment Baseline
- `rl_macro_placement_v2.py` runs as a simplified RL demo
- uses Gymnasium + Stable-Baselines3
- remains separate from the OpenROAD data path for now

## Current Reproducible Command

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad -j1
```

## Compatibility Fix Applied

Current ORFS expects a newer OpenROAD CTS interface than the installed binary supports.

Applied fix:

- remove `-repair_clock_nets` from `clock_tree_synthesis`
- call `repair_clock_nets` as a separate command after CTS

Patched file:

- `/home/DATN/OpenROAD-flow-scripts/flow/scripts/cts.tcl`

## Current Output Artifacts

Important outputs under `/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base`:

- `1_synth.odb`, `1_synth.sdc`
- `2_floorplan.odb`, `2_floorplan.sdc`
- `3_place.odb`, `3_place.sdc`
- `4_cts.odb`, `4_cts.sdc`
- `5_1_grt.odb`, `5_1_grt.sdc`
- `5_route.odb`, `5_route.sdc`
- `6_final.odb`
- `6_final.def`
- `6_final.sdc`
- `6_final.v`
- `6_final.spef`

## Known Issues

### KLayout GDS Merge

- `klayout 0.26.2` currently segfaults during `def2stream.py`
- this blocks `6_1_merged.gds`
- this does not block the current OpenROAD milestone

### GUI Performance

- remote X11 GUI is usable for light checkpoint inspection
- heavy interactive use is still laggy
- preferred workflow is terminal execution plus occasional checkpoint viewing

## Next Steps

1. Reproduce the same `6_final.*` milestone on a stronger machine.
2. Map ORFS intermediate artifacts to the RL data path.
3. Move from sample `gcd` to a `MacroPlacement` testcase.
4. Build the converter path toward `protobuf` and `initial.plc`.
5. Return to GDS/DRC/LVS only after the RL data path is stable.
