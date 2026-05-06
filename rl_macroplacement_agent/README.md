# PPO vs DREAMPlace Macro Placement Pipeline

This directory contains a lightweight, Circuit-Training-free pipeline for comparing:

- DREAMPlace: gradient-based global placement baseline.
- MaskablePPO: grid-action macro placement agent with action masking.

The shared evaluator is `MacroPlacement/CodeElements/Plc_client/plc_client_os.py`, so PPO and DREAMPlace placements are scored with the same proxy cost, wirelength, density, and congestion calls after both are converted to `.plc`.

## Setup

```bash
sudo apt-get update
sudo apt-get install -y python3-pip cmake build-essential git
python3 -m pip install -r rl_macroplacement_agent/requirements.txt
bash rl_macroplacement_agent/scripts/install_dreamplace.sh
```

If CUDA is available through `nvcc`, the DREAMPlace build script enables the CUDA compiler path. Otherwise it builds CPU-only and you should use a small benchmark.

## PPO

```bash
python3 rl_macroplacement_agent/scripts/train_maskable_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/ppo/train \
  --steps 100000 \
  --max_macros 20

python3 rl_macroplacement_agent/scripts/evaluate_policy.py \
  --model rl_macroplacement_agent/results/ariane133_ng45/ppo/train/maskable_ppo_model.zip \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/ppo/eval \
  --deterministic
```

## DREAMPlace

Run DREAMPlace with an official JSON benchmark:

```bash
python3 rl_macroplacement_agent/scripts/run_dreamplace_baseline.py \
  --dreamplace_root DREAMPlace \
  --json DREAMPlace/test/ispd2005/adaptec1.json \
  --out_dir rl_macroplacement_agent/results/dreamplace/adaptec1
```

For same-benchmark comparison, use a DREAMPlace config generated from the same design, convert its `.pl` output to `.plc`, then score it:

```bash
python3 rl_macroplacement_agent/scripts/convert_bookshelf_pl_to_plc.py \
  --dreamplace_pl path/to/dreamplace_output.pl \
  --template_plc MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --out rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace.plc

python3 rl_macroplacement_agent/scripts/eval_proxy.py \
  --netlist MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  --plc rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace.plc \
  --out rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace_metrics.json
```

## Compare

```bash
python3 rl_macroplacement_agent/scripts/compare_results.py \
  --result PPO=rl_macroplacement_agent/results/ariane133_ng45/ppo/eval/ppo_eval_summary.json \
  --result DREAMPlace=rl_macroplacement_agent/results/ariane133_ng45/dreamplace/dreamplace_metrics.json \
  --out_dir rl_macroplacement_agent/results/ariane133_ng45/comparison
```

The output table is written as JSON, CSV, and Markdown.
