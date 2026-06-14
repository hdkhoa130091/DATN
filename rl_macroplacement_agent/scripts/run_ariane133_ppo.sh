#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${PROJECT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python}"
DEVICE="${DEVICE:-cuda}"
EPISODES="${EPISODES:-10}"
ROLLOUT_EPISODES="${ROLLOUT_EPISODES:-2}"
MAX_MACROS="${MAX_MACROS:-5}"
MAX_NODES="${MAX_NODES:-1024}"
MAX_EDGES="${MAX_EDGES:-4000}"
MAX_GRID="${MAX_GRID:-32}"
BATCH_SIZE="${BATCH_SIZE:-1}"
OUT_DIR="${OUT_DIR:-rl_macroplacement_agent/results/ariane133_ng45/alphachip_like/train}"

NETLIST="MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt"
INIT_PLC="MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc"

for input in "${NETLIST}" "${INIT_PLC}"; do
  if [ ! -s "${input}" ]; then
    echo "RL input not found: ${input}"
    exit 1
  fi
done

if [ "${DEVICE}" = "cuda" ]; then
  "${PYTHON_BIN}" -c 'import torch; assert torch.cuda.is_available(), "CUDA is not available in PyTorch"; print(torch.cuda.get_device_name(0))'
fi

export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

"${PYTHON_BIN}" rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py \
  --netlist "${NETLIST}" \
  --init_plc "${INIT_PLC}" \
  --out_dir "${OUT_DIR}" \
  --episodes "${EPISODES}" \
  --rollout_episodes "${ROLLOUT_EPISODES}" \
  --max_macros "${MAX_MACROS}" \
  --max_nodes "${MAX_NODES}" \
  --max_edges "${MAX_EDGES}" \
  --max_grid "${MAX_GRID}" \
  --batch_size "${BATCH_SIZE}" \
  --device "${DEVICE}"

echo "Model and training logs saved to ${OUT_DIR}"
