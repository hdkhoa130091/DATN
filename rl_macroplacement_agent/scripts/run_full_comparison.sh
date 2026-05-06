#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NETLIST="${NETLIST:-${ROOT_DIR}/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt}"
INIT_PLC="${INIT_PLC:-${ROOT_DIR}/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc}"
RESULT_ROOT="${RESULT_ROOT:-${ROOT_DIR}/rl_macroplacement_agent/results/ariane133_ng45}"
PPO_STEPS="${PPO_STEPS:-100000}"
MAX_MACROS="${MAX_MACROS:-20}"

mkdir -p "${RESULT_ROOT}/proxy" "${RESULT_ROOT}/ppo" "${RESULT_ROOT}/comparison"

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/eval_proxy.py" \
  --netlist "${NETLIST}" \
  --plc "${INIT_PLC}" \
  --out "${RESULT_ROOT}/proxy/initial.json"

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/train_maskable_ppo.py" \
  --netlist "${NETLIST}" \
  --init_plc "${INIT_PLC}" \
  --out_dir "${RESULT_ROOT}/ppo/train" \
  --steps "${PPO_STEPS}" \
  --max_macros "${MAX_MACROS}"

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/evaluate_policy.py" \
  --model "${RESULT_ROOT}/ppo/train/maskable_ppo_model.zip" \
  --netlist "${NETLIST}" \
  --init_plc "${INIT_PLC}" \
  --out_dir "${RESULT_ROOT}/ppo/eval" \
  --max_macros "${MAX_MACROS}" \
  --deterministic

echo "PPO is evaluated. To include DREAMPlace, run run_dreamplace_baseline.py, then eval_proxy.py on its converted .plc and add DREAMPLACE=... to compare_results.py."

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/compare_results.py" \
  --result "INITIAL=${RESULT_ROOT}/proxy/initial.json" \
  --result "PPO=${RESULT_ROOT}/ppo/eval/ppo_eval_summary.json" \
  --out_dir "${RESULT_ROOT}/comparison"
