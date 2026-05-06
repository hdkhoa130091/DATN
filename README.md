# DATN Macro Placement Comparison

This workspace compares two macro-placement approaches on the same benchmark:

- **DREAMPlace**: gradient-based placement baseline.
- **MaskablePPO**: reinforcement-learning macro placer inspired by AlphaChip-style sequential placement.

The vendored `circuit_training/` tree has been removed. The active RL pipeline lives in `rl_macroplacement_agent/` and uses MacroPlacement's open `plc_client_os.py` evaluator for consistent proxy cost, wirelength, density, and congestion metrics.

## Quick Start

Install PPO-side dependencies:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip cmake build-essential git
python3 -m pip install -r rl_macroplacement_agent/requirements.txt
```

Clone, build, and smoke-test official DREAMPlace:

```bash
bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

Run the PPO smoke/comparison flow:

```bash
PPO_STEPS=1000 MAX_MACROS=5 bash rl_macroplacement_agent/scripts/run_full_comparison.sh
```

For full experiments, raise `PPO_STEPS` to `100000` or more and run DREAMPlace on a matching benchmark config, then convert its `.pl` output to `.plc` with:

```bash
python3 rl_macroplacement_agent/scripts/convert_bookshelf_pl_to_plc.py \
  --dreamplace_pl path/to/dreamplace_output.pl \
  --template_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --out rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace.plc
```

Then score and compare:

```bash
python3 rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace.plc \
  --out rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace_metrics.json

python3 rl_macroplacement_agent/scripts/compare_results.py \
  --result PPO=rl_macroplacement_agent/results/ariane133_ng45/ppo/eval/ppo_eval_summary.json \
  --result DREAMPlace=rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace_metrics.json \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/comparison
```

See `rl_macroplacement_agent/README.md` for the detailed pipeline.
