# Research Results: RL Macro Placement Toward AlphaChip / Circuit Training

_Last updated: 2026-05-17_

## 1. Research Goal

The thesis direction is **reinforcement learning for macro placement following the AlphaChip / Circuit Training line**, not only a generic PPO smoke test.

The work therefore separates two roles:

1. **Simplified baseline**: a small MaskablePPO + MLP agent used to verify the end-to-end RL pipeline and produce an interpretable baseline.
2. **Main research path**: an AlphaChip-like graph agent that observes the netlist structure and places hard macros sequentially, closer to the observation/model design used by Circuit Training.

The upstream `MacroPlacement` project motivates the final evaluation style: proxy placement metrics are useful during training, but final claims should eventually be validated with physical-design metrics such as routed wirelength, power, WNS/TNS, and congestion across stages such as `preCTS`, `postCTS`, and `postRoute`.

## 2. Experimental Setting So Far

| Item | Current setting |
|---|---|
| Platform | `NanGate45` |
| Testcase | `ariane133` |
| Netlist source | `MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/` |
| Hard macros in testcase | `133` |
| Soft macros in testcase | `782` |
| Port clusters | `14` |
| Feature graph nodes | `929` |
| Nonzero graph edges | `9,576` |
| Real placement grid | `24 x 21` |
| Main current metrics | proxy cost, wirelength, runtime |

Raw run artifacts are stored locally under:

```text
rl_macroplacement_agent/results/
```

Because this directory contains heavy checkpoints and generated artifacts, it is intentionally ignored by Git. This document records the compact, commit-friendly research summary.

## 3. Method A: Simplified MaskablePPO Baseline

### 3.1 Purpose

The first agent was intentionally simple. Its role was to verify that the project could already perform:

```text
train -> deterministic evaluation -> .plc output -> proxy metrics -> table generation
```

It is a **baseline**, not a faithful AlphaChip reproduction.

### 3.2 Observation and model

The baseline environment in `rl_macroplacement_agent/scripts/macro_env.py` uses an 8-dimensional vector observation:

```text
[current macro progress,
 previous_cost / initial_cost,
 best_cost / initial_cost,
 last_reward,
 normalized x,
 normalized y,
 normalized width,
 normalized height]
```

The policy in `train_maskable_ppo.py` is:

```python
MaskablePPO("MlpPolicy", env, ...)
```

So the baseline is an MLP policy with action masking over grid cells. It does **not** observe the full netlist graph, sparse adjacency, port clusters, or global node features.

### 3.3 Reward

The baseline uses stepwise proxy-cost improvement:

$$
r_t = \alpha \left(C_{t-1} - C_t\right)
$$

where:

- \(C_{t-1}\) is the previous proxy cost,
- \(C_t\) is the proxy cost after the current placement action,
- \(\alpha\) is the reward scaling factor.

Additional penalties are applied for invalid actions or non-improving behavior.

### 3.4 Baseline results: training budget study at 5 macros

| Steps | Macros | Runs | Eval cost mean ± std | Wirelength mean ± std | Runtime mean ± std (s) |
|---:|---:|---:|---:|---:|---:|
| 1000 | 5 | 3 | 0.053381 ± 0.000244 | 3,456,132.3 ± 15,804.4 | 84.16 ± 0.63 |
| 3000 | 5 | 3 | **0.052556 ± 0.000002** | **3,402,688.8 ± 195.3** | 242.28 ± 0.51 |
| 5000 | 5 | 3 | 0.052558 ± 0.000002 | 3,402,801.6 ± 146.3 | 409.99 ± 5.42 |

**Interpretation**

- Increasing the budget from `1000 -> 3000` steps improved the baseline materially.
- Increasing from `3000 -> 5000` steps gave almost no benefit, indicating a plateau on the 5-macro simplified task.

### 3.5 Baseline results: difficulty scaling at fixed 3000 steps

| Steps | Macros | Runs | Eval cost mean ± std | Wirelength mean ± std | Runtime mean ± std (s) |
|---:|---:|---:|---:|---:|---:|
| 3000 | 5 | 3 | **0.052556 ± 0.000002** | **3,402,688.8 ± 195.3** | 242.28 ± 0.51 |
| 3000 | 10 | 3 | 0.056654 ± 0.000310 | 3,667,979.7 ± 20,093.3 | 219.45 ± 2.10 |
| 3000 | 20 | 3 | 0.061784 ± 0.000689 | 4,000,144.8 ± 44,632.0 | 185.75 ± 1.32 |

**Interpretation**

- At a fixed training budget, the problem becomes clearly harder as more macros are moved.
- This table justifies a curriculum or budget-scaling study later, but the MLP baseline alone is not the intended final method.

## 4. Method B: AlphaChip-like Graph Agent

### 4.1 Why this method is the main thesis direction

AlphaChip / Circuit Training does not rely on a tiny local state vector. Its agent uses graph-aware observations that encode netlist structure and the current placement state. The local implementation follows that direction through:

- `alphachip_like_features.py`
- `alphachip_like_model.py`
- `train_alphachip_like_ppo.py`

### 4.2 Observation

The graph observation contains:

| Feature group | Meaning |
|---|---|
| `metadata` | global placement/netlist metadata |
| `node_features` | normalized macro/port geometry and placement state |
| `sparse_adj_i`, `sparse_adj_j`, `sparse_adj_weight` | sparse graph connectivity |
| `current_node` | macro currently being placed |
| `mask` | feasible grid cells on the padded placement canvas |

For `ariane133`, the smoke test confirmed:

| Tensor / property | Observed value |
|---|---:|
| `feature_nodes` | 929 |
| `hard_macros` | 133 |
| `soft_macros` | 782 |
| `port_clusters` | 14 |
| `nonzero_edges` | 9,576 |
| `node_features` shape | `[5000, 8]` |
| sparse adjacency shape | `[70000]` |
| padded action mask shape | `[16384]` |

### 4.3 Model

The local actor-critic is intentionally AlphaChip-like rather than a drop-in reproduction. It includes:

1. metadata encoder,
2. node encoder,
3. edge-centric graph message passing,
4. attention from the current macro to the graph,
5. grid policy head,
6. value head.

Conceptually:

```text
metadata + graph node features + sparse edges
    -> message passing
    -> current-macro attention over graph
    -> grid logits + value estimate
```

### 4.4 PPO objective and terminal reward

The current AlphaChip-like trainer uses terminal proxy reward:

$$
R = \alpha \left(C_{\mathrm{init}} - C_{\mathrm{final}}\right)
$$

where \(C_{\mathrm{init}}\) is the proxy cost before the episode, \(C_{\mathrm{final}}\) is the proxy cost after the final hard-macro placement, and \(\alpha\) is the reward scaling factor.

The actor is optimized with the clipped PPO objective:

$$
\mathcal{L}_{\mathrm{policy}}
=
-\mathbb{E}_t
\left[
\min
\left(
\rho_t A_t,\;
\operatorname{clip}\!\left(\rho_t, 1-\epsilon, 1+\epsilon\right) A_t
\right)
\right]
$$

where:

$$
\rho_t
=
\frac{\pi_{\theta}\!\left(a_t \mid s_t\right)}
{\pi_{\theta_{\mathrm{old}}}\!\left(a_t \mid s_t\right)}
$$

The critic uses squared value error, and the total loss is:

$$
\mathcal{L}
=
\mathcal{L}_{\mathrm{policy}}
+
c_v \mathcal{L}_{\mathrm{value}}
-
c_e \mathcal{H}
$$

with:

$$
\mathcal{L}_{\mathrm{value}}
=
\mathbb{E}_t \left[\left(G_t - V_{\phi}(s_t)\right)^2\right]
$$

where \(\mathcal{H}\) is the policy entropy term, \(c_v\) is the value-loss coefficient, \(c_e\) is the entropy coefficient, and \(G_t\) is the return target.

Advantages are computed with generalized advantage estimation (GAE):

$$
A_t
=
\delta_t
+
\gamma \lambda \left(1-d_t\right) A_{t+1}
$$

$$
\delta_t
=
r_t
+
\gamma \left(1-d_t\right) V_{\phi}(s_{t+1})
-
V_{\phi}(s_t)
$$

where \(d_t \in \{0,1\}\) is the episode-termination indicator.

## 5. Important Debugging Findings and Fixes

These findings are part of the research result because they changed the validity of later experiments.

### 5.1 Fix 1: advantage normalization was done at the wrong level

**Problem**

Originally, the AlphaChip-like trainer normalized advantages independently inside each short episode. With terminal reward and only 5 placement steps in the early experiments, this destroyed useful comparisons between good and bad episodes before PPO saw the combined rollout batch.

**Fix**

- keep per-episode advantages raw,
- concatenate multiple episodes,
- normalize once across the full PPO rollout batch.

**Evidence**

| Run | Condition | Eval cost | Wirelength |
|---|---|---:|---:|
| `ac002` | before fix | 0.054360 | 3,519,498 |
| `ac003` | after fix | **0.052516** | **3,400,111** |

Additional learning signals changed in the expected direction after the fix:

- entropy collapsed from about `2.98` to about `0.44`,
- `clip_fraction` became nonzero,
- final episode costs improved over training instead of staying flat.

### 5.2 Fix 2: AlphaChip-like episodes did not reset like Circuit Training

**Problem**

The earlier AlphaChip-like loop restored `initial.plc` but did not unplace movable nodes before the hard-macro sequence. The initial placement contains:

| Node group | Count initially placed |
|---|---:|
| hard macros | 133 |
| soft macros | 782 |
| total placed macros | 915 |

The action mask therefore treated nearly the whole existing placement as obstacles while asking the agent to place more hard macros.

For the first selected macro:

| Episode setup | Valid cells |
|---|---:|
| keep all initial placed macros | 24 |
| unplace only the selected 20 macros | 26 |
| unplace all hard macros | 175 |
| unplace all movable nodes | **456** |

Under the old setup, a 20-macro rollout exhausted its legal cells:

```text
step 1: 24 valid cells
...
step 16: 1 valid cell
step 17: 0 valid cells
```

**Why this was incorrect**

Circuit Training-style macro placement starts from a reset state in which movable nodes are unplaced before the hard macros are placed sequentially. Keeping the entire old placement as obstacles changed the task into a nearly impossible re-packing problem that AlphaChip is not intended to solve.

**Fix**

The trainer and evaluator now call:

```python
plc.unplace_all_nodes()
```

before the hard-macro placement sequence, and they stop explicitly if a mask is empty.

**Verification after the fix**

Using the same 20-macro policy checkpoint after the environment fix:

| Step | Valid cells |
|---:|---:|
| 1 | 456 |
| 20 | 404 |

The evaluation completed all `20 / 20` placements with:

```text
invalid_action = null
```

## 6. AlphaChip-like Manual Runs at 5 Macros

### 6.1 Before and after the trainer fix

| Run | Episodes | Seed | Condition | Eval cost | Wirelength |
|---|---:|---:|---|---:|---:|
| `ac001` | 205 | 1 | early smoke run | 0.054424 | 3,523,662 |
| `ac002` | 615 | 1 | before advantage fix | 0.054360 | 3,519,498 |
| `ac003` | 615 | 1 | after advantage fix | **0.052516** | **3,400,111** |
| `ac004` | 615 | 2 | after advantage fix | 0.052592 | 3,404,999 |
| `ac005` | 615 | 3 | after advantage fix | 0.052950 | 3,428,181 |

### 6.2 Three-seed comparison with the MLP baseline

| Model | Budget | Eval cost mean ± std | Wirelength mean ± std | Runtime mean ± std (s) |
|---|---:|---:|---:|---:|
| MLP baseline | 3000 steps | **0.052556 ± 0.000003** | **3,402,688.8 ± 195.3** | 242.28 ± 0.51 |
| AlphaChip-like | 3075 steps | 0.052686 ± 0.000232 | 3,411,097.0 ± 14,995.7 | 318.47 ± 0.75 |

**Interpretation**

- On the very small 5-macro task, the simple MLP baseline is already strong and more stable.
- This is not evidence against the graph model; it means the graph model's advantage should be tested on harder tasks where topology matters more.

## 7. Curriculum Learning Experiments

### 7.1 Curriculum definition used here

The local curriculum increases the number of hard macros handled by one policy:

```text
5 macros -> 10 macros -> 20 macros
```

Each later stage resumes from the previous checkpoint. A scratch 20-macro run with the same seed and episode budget is trained as the control.

### 7.2 Invalid pilot run that should not be used for final claims

`cur001` was run before the environment reset bug was fixed. It suggested curriculum helped, but all 20-macro episodes had invalid actions and therefore the result is only useful as a debugging record, not as a scientific comparison.

### 7.3 Clean short-budget curriculum: `cur002`

| Method | Episodes/stage | 20-macro eval cost | 20-macro wirelength |
|---|---:|---:|---:|
| curriculum | 256 | 0.059928 | 3,879,962 |
| scratch | 256 | **0.058772** | **3,805,118** |

**Interpretation**

With too little budget per stage, curriculum did not outperform scratch.

### 7.4 Clean longer-budget curriculum: `cur003`

| Method | Episodes/stage | 20-macro eval cost | 20-macro wirelength |
|---|---:|---:|---:|
| curriculum | 615 | **0.054444** | **3,524,934** |
| scratch | 615 | 0.061006 | 3,949,756 |

Relative gain of curriculum over scratch at 20 macros:

```text
Eval cost improvement     ~= 10.76%
Wirelength improvement    ~= 10.76%
```

Training behavior also supports the conclusion:

| Run | Mean final cost first 20 episodes | Mean final cost last 20 episodes |
|---|---:|---:|
| curriculum stage 3, 20 macros | 0.058023 | **0.055221** |
| scratch 20 macros | 0.059875 | 0.059914 |

**Current conclusion**

The present evidence supports:

> Curriculum over macro-count difficulty can help the AlphaChip-like graph agent, but only when each stage receives enough training budget.

This conclusion is currently established for `seed = 1`; it still needs repeated-seed confirmation.

## 8. What Is Valid to Claim Now

### Supported claims

1. The local open-source flow can train and evaluate macro-placement RL agents end-to-end.
2. The original 8-value MLP agent is a useful baseline but is not architecturally close to Circuit Training.
3. The AlphaChip-like graph path runs end-to-end on the MacroPlacement dataset.
4. Advantage normalization across the full rollout batch is necessary for meaningful PPO learning in the current trainer.
5. Correct Circuit Training-style reset semantics require unplacing movable nodes before sequential hard-macro placement.
6. With a sufficient stage budget, curriculum transfer from `5 -> 10 -> 20` macros can substantially outperform scratch training at 20 macros on `ariane133` seed 1.

### Claims not yet supported

1. AlphaChip-like is globally better than MLP across all task sizes.
2. Curriculum is robust across seeds; only the clean long-budget `seed = 1` result exists so far.
3. The method scales successfully to the full `133` hard macros yet.
4. Proxy-cost gains already imply final post-route chip-quality gains.

## 9. Relation to MacroPlacement-style Evaluation

The current tables are **training/proxy tables**. To complete a study comparable in spirit to `MacroPlacement`, the project must still add a physical-design evaluation layer:

1. export selected RL placements back into the OpenROAD / P&R flow,
2. run physical implementation stages,
3. extract metrics aligned with MacroPlacement tables:
   - wirelength,
   - power,
   - WNS,
   - TNS,
   - congestion,
   - ideally at `preCTS`, `postCTS`, and `postRoute`.

The final thesis should separate:

| Table type | Purpose |
|---|---|
| proxy/training table | what the agent optimized and learned |
| physical table | what the final chip implementation achieved |

## 10. Recommended Next Research Plan

### Phase 1: confirm the curriculum effect

1. Repeat the clean long-budget experiment at `seed = 2`:

```bash
bash rl_macroplacement_agent/scripts/run_alphachip_like_curriculum.sh \
  NanGate45 ariane133 cur004 2 615 5,10,20
```

2. Repeat at `seed = 3` if seed 2 is consistent.
3. Report mean ± std for:
   - curriculum 20-macro final stage,
   - scratch 20-macro control.

### Phase 2: scale the curriculum

If repeated seeds remain favorable, extend difficulty gradually:

```text
5 -> 10 -> 20 -> 50 -> 100 -> 133 hard macros
```

Because episode length grows with macro count, the total step budget should be scaled deliberately instead of keeping a tiny fixed number of steps for larger tasks.

### Phase 3: strengthen baselines and ablations

Recommended comparisons:

1. scratch vs curriculum,
2. MLP baseline vs AlphaChip-like graph model,
3. short-stage vs long-stage curriculum budget,
4. possibly alternative curricula such as:
   - more stages,
   - repeated warm-up at fixed macro count,
   - transfer by testcase after single-netlist convergence.

### Phase 4: move toward MacroPlacement-comparable claims

1. choose representative placements from repeated-seed RL runs,
2. run OpenROAD / P&R evaluation,
3. create tables analogous to MacroPlacement's physical evaluation tables,
4. compare against baselines such as scratch, MLP, and if feasible DREAMPlace/OpenROAD-generated placements.

## 11. Reproducibility Pointers

Key scripts:

```text
rl_macroplacement_agent/scripts/run_manual_ppo_run.sh
rl_macroplacement_agent/scripts/run_manual_alphachip_like_run.sh
rl_macroplacement_agent/scripts/run_alphachip_like_curriculum.sh
rl_macroplacement_agent/scripts/train_maskable_ppo.py
rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py
rl_macroplacement_agent/scripts/alphachip_like_features.py
rl_macroplacement_agent/scripts/alphachip_like_model.py
```

Key local result tables:

```text
rl_macroplacement_agent/results/manual_runs/NanGate45/ariane133/tables/run_table.csv
rl_macroplacement_agent/results/manual_runs/NanGate45/ariane133/tables/run_table.md
rl_macroplacement_agent/results/curriculum_runs/NanGate45/ariane133/cur002/curriculum_table.csv
rl_macroplacement_agent/results/curriculum_runs/NanGate45/ariane133/cur003/curriculum_table.csv
```

## 12. Current Bottom Line

The project has moved beyond setup and smoke testing. It now has:

- a working open-source RL macro-placement pipeline,
- a simplified baseline,
- a graph-based AlphaChip-like policy path,
- two important correctness fixes,
- a clean curriculum result showing a strong 20-macro gain at sufficient budget,
- and a concrete path to finish the study in a way that becomes comparable to MacroPlacement-style evaluation.
