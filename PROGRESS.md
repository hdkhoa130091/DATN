# RL Macro Placement Project - Progress Summary

## 2026-05-17 - AlphaChip-like Study Consolidated

### Current Research Direction

The project direction is now explicitly:

```text
RL macro placement toward AlphaChip / Circuit Training
```

The small `MaskablePPO + MLP` environment is retained as a baseline, while the
main method is the graph-based AlphaChip-like path in:

```text
rl_macroplacement_agent/scripts/alphachip_like_features.py
rl_macroplacement_agent/scripts/alphachip_like_model.py
rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py
```

A commit-friendly research summary has been written to:

```text
RESULTS.md
```

That document records the experiment purpose, theory, formulas, debugging
findings, valid/invalid claims, tables, conclusions, and the next path toward a
MacroPlacement-style final evaluation.

### Main Findings Completed In This Stage

1. The first AlphaChip-like PPO trainer normalized advantages per episode,
   which suppressed useful cross-episode learning signal. Advantage
   normalization was moved to the concatenated rollout batch.
2. The earlier AlphaChip-like environment restored `initial.plc` but did not
   unplace movable nodes before sequential hard-macro placement. That left 915
   already-placed macros as artificial obstacles and exhausted the 20-macro mask
   by about step 17. The trainer and evaluator now call `unplace_all_nodes()` to
   match Circuit Training-style reset semantics.
3. After the fixes, all clean 20-macro runs complete the full placement sequence
   without invalid actions.
4. A short clean curriculum (`cur002`, 256 episodes/stage) did not beat scratch,
   but a longer clean curriculum (`cur003`, 615 episodes/stage) did:

| method at 20 macros | eval cost | wirelength |
|---|---:|---:|
| curriculum 5 -> 10 -> 20 | 0.0544441094 | 3524933.8925 |
| scratch 20 | 0.0610056629 | 3949755.6562 |

This is a roughly 10.76% improvement in both eval cost and wirelength for the
clean long-budget seed-1 comparison.

### Immediate Next Step

Repeat the clean long-budget curriculum with additional seeds before scaling to
larger macro counts:

```bash
bash rl_macroplacement_agent/scripts/run_alphachip_like_curriculum.sh \
  NanGate45 ariane133 cur004 2 615 5,10,20
```

If repeated seeds confirm the effect, extend the study toward:

```text
5 -> 10 -> 20 -> 50 -> 100 -> 133 hard macros
```

and then add OpenROAD / post-P&R evaluation tables closer to the style used in
`MacroPlacement`.

## 2026-05-16 - Researching MacroPlacement Evaluation Protocol

### Goal

Before running a large batch of experiments, study how the upstream
`TILOS-AI-Institute/MacroPlacement` project evaluates macro placement methods
and use that protocol to decide what tables should be produced for this thesis.

### What Was Learned From MacroPlacement

The upstream project uses two complementary levels of evaluation:

1. **Proxy-placement metrics**
   - wirelength cost
   - density cost
   - congestion cost
   - weighted proxy cost
2. **Post-P&R chip metrics**
   - core area
   - standard-cell area
   - macro area
   - total power
   - routed wirelength
   - WNS
   - TNS
   - congestion

The second group is extracted at three physical-design stages:

```text
preCTS -> postCTS -> postRoute
```

using `MacroPlacement/Flows/util/extract_report.tcl`. The corresponding CSV
files are stored under `MacroPlacement/ExperimentalData/`.

Important methodological lesson:

```text
Do not evaluate RL only by reward or proxy cost.
Proxy metrics are useful for training, but final claims should also use
post-P&R chip metrics whenever the flow is available.
```

### How This Applies To Our RL Work

For the current open-source RL stage, the first table should be a
**training/evaluation table** over repeated runs:

| testcase | steps | moved macros | seed count | best proxy cost | eval proxy cost | runtime |
|---|---:|---:|---:|---:|---:|---:|

Recommended aggregation:

- one row per `(testcase, steps, moved_macros)`
- run at least three seeds
- report `mean ± std`
- keep all raw runs in CSV/JSON so every summary number is traceable

Later, after placements are fed back into OpenROAD or a full P&R flow, add a
second table closer to MacroPlacement's style:

| testcase | method | stage | wirelength | power | WNS | TNS | congestion |
|---|---|---|---:|---:|---:|---:|---:|

This separates:

- **what the RL agent optimized**
- **what the final chip implementation achieved**

### Code Added For Future Runs

Added:

- `rl_macroplacement_agent/scripts/run_maskable_ppo_matrix.py`
- `rl_macroplacement_agent/scripts/run_manual_ppo_run.sh`

This script is kept as a reusable experiment launcher, but no generated result
files are retained in the repository state. It can execute a matrix over:

- training steps
- number of moved macros
- random seeds

and write:

- `matrix_runs.csv`
- `matrix_runs.json`
- `matrix_summary.csv`
- `matrix_summary.json`
- `matrix_summary.md`

`run_manual_ppo_run.sh` is the preferred launcher when experiments are being
recorded one run at a time for a thesis table. It uses absolute paths, so it can
be invoked from any current working directory, and it performs the complete
per-run sequence:

```text
train -> deterministic eval -> .plc to Tcl -> CSV row -> Markdown table
```

### Small Cleanup

Updated `train_maskable_ppo.py` to read callback attributes from
`env.unwrapped`, removing Gymnasium deprecation warnings in future runs.

Temporary auto-run result folders created during exploration were removed so the
next experiment batch can be run manually and recorded intentionally.

### OpenROAD Visualization Findings

Two important integration issues were identified while preparing GUI viewing:

1. Running ORFS macro floorplanning for the copied `ariane133` design currently
   stops at `2_2_floorplan_macro` with `MPL-0002`. This does not block RL runs.
2. The ORFS-synthesized `ariane133` checkpoint is not the right visualization
   base for RL placements from the MacroPlacement dataset:
   - ORFS checkpoint observed: 44 macros
   - RL dataset placement: 133 hard macros

For RL placement visualization, the correct base is instead:

```text
MacroPlacement/Flows/NanGate45/ariane133/def/Util_51/ariane133_fp_placed_macros.def
```

with the NanGate45 LEFs loaded directly in OpenROAD. The DEF-loaded database
uses escaped bracket names such as `macro_mem\\[0\\]`, so
`plc_to_openroad_tcl.py` now supports `--escape_brackets`. The installed
OpenROAD build also does not accept `place_macro -exact`, so manual-run Tcl is
generated without `-exact`.

Each manual run now generates:

```text
openroad/view_best_rl.tcl
openroad/view_ppo_final.tcl
```

These files can be sourced directly inside `openroad -gui` to load the correct
LEFs, matching DEF, and the run-specific placement.

### First Manual Run Recorded

The first verified one-by-one run was executed with:

```text
testcase: NanGate45 / ariane133
steps:    1000
macros:   5
seed:     1
```

Result:

| run | train best cost | deterministic eval cost | eval wirelength |
|---|---:|---:|---:|
| run_001_steps1000_macros5_seed1 | 0.0497221350 | 0.0537140795 | 3477668.7797 |

The run directory is:

```text
rl_macroplacement_agent/results/manual_runs/NanGate45/ariane133/run_001_steps1000_macros5_seed1/
```

### Next Research Step

1. Reproduce a small table on one testcase first, following the repeated-run
   protocol above.
2. Extend from `ariane133` to additional available MacroPlacement benchmarks
   such as `ariane136`, `mempool_tile`, and `nvdla`.
3. Decide whether the report should emphasize:
   - only RL learning behavior at the current stage, or
   - the full `RL -> .plc -> OpenROAD/P&R` quality comparison.

## 2026-05-08 - Custom PyTorch AlphaChip-Like PPO Smoke Test

### Goal

This step connects the newly added graph observation extractor to the explicit
PyTorch model and PPO agent.

The flow now has a first custom end-to-end AlphaChip-like training path:

```text
PlacementCost
  -> AlphaChipLikeFeatureExtractor
  -> AlphaChipLikeActorCritic
  -> AlphaChipLikePPOAgent
  -> placement action
  -> terminal proxy reward
  -> PPO update
```

This is still a smoke-test trainer, not a distributed AlphaChip reproduction.
Its purpose is to make the local `model + agent + training loop` visible and
explainable.

### Code Added

Added:

- `rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py`

The script implements:

- model initialization with configurable graph sizes
- one-episode rollout collection
- padded AlphaChip-like grid action conversion back to real MacroPlacement grid
- action-mask based sampling through `AlphaChipLikeActorCritic`
- terminal reward based on proxy-cost improvement
- GAE/return computation through `AlphaChipLikePPOAgent`
- one PPO update per collected episode
- model checkpoint and CSV/JSON training logs

### Smoke Test

Command:

```bash
DATA=/home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping
/home/DATN/rl_env/bin/python rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py \
  --netlist $DATA/netlist.pb.txt \
  --init_plc $DATA/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/alphachip_like_ppo_smoke \
  --episodes 1 \
  --max_macros 2 \
  --max_nodes 1024 \
  --max_edges 12000 \
  --max_grid 32 \
  --device cpu
```

Observed result:

```text
episodes: 1
max_macros: 2
initial_cost: 0.04972213503402197
final_cost:   0.052089277825661785
episode_reward: -2.367142677307129
invalid_action: none
loss: 3.2872743606567383
value_loss: 6.636768817901611
entropy: 3.1110033988952637
```

Output artifacts:

```text
rl_macroplacement_agent/results/ariane133_ng45/alphachip_like_ppo_smoke/alphachip_like_actor_critic.pt
rl_macroplacement_agent/results/ariane133_ng45/alphachip_like_ppo_smoke/alphachip_like_training_history.csv
rl_macroplacement_agent/results/ariane133_ng45/alphachip_like_ppo_smoke/alphachip_like_train_summary.json
```

Interpretation:

- the custom PyTorch AlphaChip-like PPO path runs end-to-end
- graph observations feed the model
- the model samples valid masked placement actions
- `PlacementCost` computes a terminal proxy reward
- the PPO agent performs an optimizer update
- the placement quality did not improve in this tiny smoke test, which is
  expected because it only used one episode and two macros

### Next Improvement

The next technical step is to make this trainer useful beyond smoke testing:

1. cache static graph tensors to avoid rebuilding them every episode
2. train with more episodes and more macros
3. save the best custom-PPO `.plc`
4. compare custom PyTorch PPO against the existing Stable-Baselines3
   MaskablePPO baseline
5. add optional DREAMPlace/OpenROAD evaluation after macro placement

## 2026-05-08 - AlphaChip-Like Graph Observation Extractor

### Goal

This step starts the planned improvement after the initial PyTorch
AlphaChip-like model and PPO agent prototype.

The main problem in the first running RL code was that the environment only
returned an 8-value observation vector. That observation is too weak for macro
placement because it does not expose the circuit graph, macro connectivity,
node types, port clusters, or action masks in the same style as
`circuit_training`.

This update adds an AlphaChip-like observation extraction layer.

### Code Added

Added:

- `rl_macroplacement_agent/scripts/alphachip_like_features.py`
- `rl_macroplacement_agent/scripts/inspect_alphachip_like_features.py`

`alphachip_like_features.py` builds model-ready graph observations from
`plc_client_os.PlacementCost`:

- 12-value netlist metadata vector
- macro/soft-macro/port-cluster node features
- sparse adjacency arrays `sparse_adj_i`, `sparse_adj_j`, `sparse_adj_weight`
- edge-count vector
- current-node feature index
- padded grid action mask

The observation keys are intentionally close to public `circuit_training`
concepts:

```text
metadata
node_features
sparse_adj_i
sparse_adj_j
sparse_adj_weight
edge_counts
netlist_index
current_node
mask
```

`inspect_alphachip_like_features.py` is a smoke-test script that:

- restores a `.plc` placement
- creates the AlphaChip-like graph observation
- reports tensor shapes
- optionally runs a forward pass through `AlphaChipLikeActorCritic`

### Smoke Test

Command:

```bash
DATA=/home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping
/home/DATN/rl_env/bin/python rl_macroplacement_agent/scripts/inspect_alphachip_like_features.py \
  --netlist $DATA/netlist.pb.txt \
  --init_plc $DATA/initial.plc \
  --max_nodes 2048 \
  --max_edges 20000 \
  --max_grid 32 \
  --run_model \
  --out rl_macroplacement_agent/results/ariane133_ng45/alphachip_like_model_smoke.json
```

Observed result:

```text
feature_nodes: 929
macro_nodes: 915
hard_macros: 133
soft_macros: 782
port_clusters: 14
nonzero_edges: 9576
grid: 24 x 21
selected_node: 495
selected_node_valid_actions: 24
```

Observation shapes:

```text
metadata:          [12]
node_features:     [2048, 8]
sparse_adj_i:      [20000]
sparse_adj_j:      [20000]
sparse_adj_weight: [20000]
edge_counts:       [2048]
current_node:      [1]
mask:              [1024]
```

Model forward smoke test:

```text
logits_shape: [1, 1024]
value_shape:  [1]
argmax_action: 347
```

Interpretation:

- the project now has a richer AlphaChip-like graph observation path
- the observation can feed the PyTorch `AlphaChipLikeActorCritic`
- this is not full training yet, but it removes the biggest architectural gap:
  the model can now receive graph/connectivity features instead of only 8 scalar
  values

### Next Improvement

The next step is to integrate this observation extractor into a custom training
loop:

```text
AlphaChipLikeFeatureExtractor
  -> AlphaChipLikeActorCritic
  -> AlphaChipLikePPOAgent
  -> placement actions
  -> PlacementCost reward
```

After that, compare:

```text
Stable-Baselines3 MaskablePPO baseline
vs
custom PyTorch AlphaChip-like PPO

## 2026-05-16 - AlphaChip-Like Manual-Run Workflow Added

The experimental workflow has now been upgraded so the graph-based
`AlphaChipLikePPO` path can be run beside the existing `MaskablePPO` baseline
instead of living only as a smoke-test trainer.

### What changed

- Removed generated Python cache files under `rl_macroplacement_agent/scripts/__pycache__`.
- Added `evaluate_alphachip_like_policy.py` to run deterministic evaluation,
  save `alphachip_like_final.plc`, and report proxy metrics.
- Added `run_manual_alphachip_like_run.sh` so AlphaChip-like runs follow the
  same manual-run folder structure as MaskablePPO.
- Added `render_manual_run_table.py` and migrated the shared CSV schema so one
  table can hold both agents:
  - `agent`
  - `episodes`
  - `train_runtime_sec`
  - `eval_runtime_sec`
- Added training-runtime capture to both training paths.
- Reduced AlphaChip-like default padding for `ariane133` from `2048/20000`
  nodes/edges to `1024/10000`; the testcase currently needs 929 feature nodes
  and 9576 nonzero edges, so the smaller default still fits while wasting less
  compute.

### New command

```bash
bash rl_macroplacement_agent/scripts/run_manual_alphachip_like_run.sh \
  NanGate45 ariane133 ac001 205 5 1
```

This creates:

```text
results/manual_runs/NanGate45/ariane133/
  run_ac001_alphachip_like_episodes205_macros5_seed1/
    train/
    eval/
    openroad/
  tables/run_table.csv
  tables/run_table.md
```

### Smoke-test result

The first AlphaChip-like workflow smoke test succeeded:

```text
run_id:             run_acsmoke_alphachip_like_episodes1_macros5_seed1
agent:              AlphaChipLikePPO
train best cost:    0.0544698176
eval cost:          0.0543939595
wirelength:         3521686.9829
train runtime:      46.91 s
eval runtime:       32.51 s
```

The output `.plc` and OpenROAD Tcl files were created correctly.

### Current interpretation

The workflow is now ready for **direct comparison** against MaskablePPO, but the
AlphaChip-like implementation is not yet efficient enough for a large sweep:

- one 5-macro episode is already much slower than MaskablePPO evaluation
- the graph policy still recomputes rich dynamic features repeatedly
- the custom trainer updates from very small batches, so quality is not yet
  expected to beat the baseline

Therefore the next technical task should be:

```text
optimize graph-observation refresh and batching
before launching many AlphaChip-like runs
```

This preserves the research direction while avoiding an expensive but
misleading large experiment.

## 2026-05-16 - AlphaChip-Like Runtime Optimization Before Large Comparison

Before launching a large AlphaChip-like vs MaskablePPO sweep, the
AlphaChip-like path was profiled and optimized.

### Profile finding

For one CPU-profiled 5-macro episode before optimization:

```text
total episode time:       57.24 s
wirelength computation:   39.41 s
node-mask generation:     10.92 s
model forward passes:      0.22 s
```

This showed that the main bottleneck was **not** the GNN itself. Most time was
spent in repeated proxy-cost plumbing around it.

### Changes made

- Added `placement_cost_optimizations.py` and reused the fast HPWL cache in both
  MaskablePPO and AlphaChip-like flows.
- Replaced the slow Python `get_node_mask()` loop in AlphaChip-like observation
  generation with a vectorized NumPy mask implementation.
- Verified the new vectorized mask against the original implementation for the
  first five `ariane133` hard macros:

```text
all compared masks matched exactly
```

- Stopped copying immutable static graph tensors for every placement step.
- Reused one `PlacementCost` object and one graph extractor across AlphaChip-like
  training episodes, resetting only placement state.
- Upgraded PPO updating from one tiny episode at a time to batched rollouts:
  - new `--rollout_episodes`
  - concatenate complete episodes before PPO update
  - run shuffled minibatch PPO epochs

### Measured improvement

After optimization, the same CPU-profiled 5-macro episode became:

```text
total episode time:        7.76 s
wirelength computation:    0.60 s
mask generation:           no longer a dominant cost
```

That is approximately:

```text
57.24 s -> 7.76 s
7.4x faster per profiled episode
```

The manual workflow smoke test also improved substantially:

```text
before optimization:
  train runtime: 46.91 s
  eval runtime:  32.51 s

after optimization:
  train runtime:  4.65 s
  eval runtime:   0.74 s
```

Temporary smoke-test result folders and rows were removed after verification so
the main experiment table remains clean.

### Current conclusion

The AlphaChip-like branch is now fast enough to begin meaningful direct
comparison against MaskablePPO. It is still architecturally more expensive than
the baseline, but the previous runtime gap was mostly avoidable implementation
overhead rather than an inherent cost of graph RL.

## 2026-05-16 - Curriculum Performance Pipeline and Full 133-Macro Study

After confirming that runtime alone is not the research target, the study moved
from a speed-oriented workflow to a **performance-oriented curriculum pipeline**.
The goal is now to measure whether staged training improves placement quality
relative to direct training from scratch at the same final difficulty.

### New performance workflow

Added:

- checkpoint resume support in `train_alphachip_like_ppo.py`
  - `--resume_from`
  - `--stage_name`
- `run_alphachip_like_curriculum.sh`
  - trains a staged path such as `5 -> 10 -> 20 -> 40 -> 80 -> 133`
  - also trains a scratch baseline at the final macro count
- `render_curriculum_table.py`
  - reports:
    - `eval_cost`
    - `wirelength`
    - `% improvement_vs_initial`
    - train runtime
- optional resume support in `run_manual_alphachip_like_run.sh`

The key experimental comparison is now:

```text
curriculum final-stage model
vs
scratch model trained directly at the same final macro count
```

### Early curriculum findings

Small studies on `ariane133` showed:

- at `10` macros, curriculum had only a weak advantage over scratch on average
- at `20` macros, curriculum again showed a small average advantage but not a
  decisive margin
- therefore the study continued to the full `133`-macro problem before making a
  stronger conclusion

### Full curriculum experiment

Three seeds were run with:

```text
episodes per stage: 128
curriculum: 5 -> 10 -> 20 -> 40 -> 80 -> 133
final scratch baseline: 133
seeds: 1, 2, 3
```

Measured full-run time for one seed to `133` macros was about:

```text
22 minutes total training time
```

### Table: Curriculum scalability on `ariane133`

| Number of macros | Mean eval cost | Std eval cost | Mean wirelength |
|---:|---:|---:|---:|
| 5 | 0.053821 | 0.001027 | 3,484,592.74 |
| 10 | 0.057682 | 0.000576 | 3,734,600.15 |
| 20 | 0.061401 | 0.000146 | 3,975,349.53 |
| 40 | 0.061859 | 0.000501 | 4,005,028.59 |
| 80 | 0.061784 | 0.000581 | 4,000,155.18 |
| 133 | 0.061090 | 0.000054 | 3,955,192.28 |

### Table: Curriculum vs scratch at full `133` macros

| Training strategy | Mean eval cost | Std eval cost | Mean wirelength |
|---|---:|---:|---:|
| Scratch training at 133 macros | 0.062282 | 0.000999 | 4,032,402.37 |
| Curriculum training `5->10->20->40->80->133` | 0.061090 | 0.000054 | 3,955,192.28 |

### Per-seed comparison at `133` macros

| Seed | Scratch eval cost | Curriculum eval cost | Curriculum improvement |
|---:|---:|---:|---:|
| 1 | 0.062499 | 0.061150 | 2.16% |
| 2 | 0.063155 | 0.061045 | 3.34% |
| 3 | 0.061193 | 0.061074 | 0.19% |

### Current interpretation

At the full `133`-macro difficulty, curriculum learning outperformed direct
scratch training for all three seeds:

```text
mean eval cost:
  scratch:    0.062282
  curriculum: 0.061090

mean improvement of curriculum over scratch:
  about 1.91%
```

Curriculum also reduced result variance substantially:

```text
scratch std:    0.000999
curriculum std: 0.000054
```

This supports the research claim that staged curriculum training improves both
placement quality and stability relative to direct training from scratch on the
full macro-placement task.

### Important metric caveat

The current metric files contain:

- valid `cost`
- valid `wirelength`
- valid `density_cost`
- invalid `congestion_cost`

The current `congestion_cost` call still returns:

```text
IndexError('list index out of range')
```

Therefore, current report tables should only use:

- `cost`
- `wirelength`
- `density_cost` only with caution, because it remained effectively constant
  across these runs

`congestion_cost` should be fixed before claiming a complete multi-objective
placement comparison.

### Current research conclusion

The project has now demonstrated:

1. an AlphaChip-like graph PPO path that runs end-to-end
2. a practical curriculum training pipeline with checkpoint transfer
3. successful scaling to the complete `ariane133` testcase
4. measurable curriculum benefit over scratch training at `133` macros

The next performance-focused phase should no longer spend most effort on larger
sweeps. The higher-value work is now:

1. fix congestion evaluation
2. improve reward shaping
3. investigate local-refinement formulations that do not destroy the strong
   initial placement
4. add best-of-k evaluation and report success rate versus `initial.plc`
```

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
