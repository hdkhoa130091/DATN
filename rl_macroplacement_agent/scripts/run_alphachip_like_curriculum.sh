#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/rl_env/bin/python}"

usage() {
  cat <<'EOF'
Usage:
  run_alphachip_like_curriculum.sh PLATFORM TESTCASE EXPERIMENT_ID SEED EPISODES_PER_STAGE MACRO_STAGES

Example:
  bash rl_macroplacement_agent/scripts/run_alphachip_like_curriculum.sh \
    NanGate45 ariane133 cur001 1 64 5,10,20
EOF
}

if [[ $# -ne 6 ]]; then
  usage
  exit 2
fi

PLATFORM="$1"
TESTCASE="$2"
EXPERIMENT_ID="$3"
SEED="$4"
EPISODES_PER_STAGE="$5"
IFS=',' read -r -a STAGES <<<"$6"

DATA_DIR="${ROOT_DIR}/MacroPlacement/Flows/${PLATFORM}/${TESTCASE}/netlist/output_CT_Grouping"
RESULT_ROOT="${ROOT_DIR}/rl_macroplacement_agent/results/curriculum_runs/${PLATFORM}/${TESTCASE}/${EXPERIMENT_ID}"
TABLE_CSV="${RESULT_ROOT}/curriculum_table.csv"
mkdir -p "${RESULT_ROOT}"

echo "run_id,mode,stage,macros,seed,episodes,initial_cost,train_best_cost,eval_cost,wirelength,train_runtime_sec,eval_runtime_sec,resume_from,run_dir" >"${TABLE_CSV}"

append_row() {
  local run_id="$1" mode="$2" stage="$3" macros="$4" episodes="$5" run_dir="$6" resume_from="$7"
  "${PYTHON_BIN}" - "${TABLE_CSV}" "${run_id}" "${mode}" "${stage}" "${macros}" "${SEED}" "${episodes}" "${run_dir}" "${resume_from}" <<'PY'
import csv, json, sys
from pathlib import Path
p=Path(sys.argv[1])
run_id,mode,stage,macros,seed,episodes,run_dir,resume_from=sys.argv[2:]
run_dir=Path(run_dir)
train=json.loads((run_dir/'train'/'alphachip_like_train_summary.json').read_text())
eval_=json.loads((run_dir/'eval'/'alphachip_like_eval_summary.json').read_text())
with p.open('a',newline='') as f:
 w=csv.writer(f)
 w.writerow([run_id,mode,stage,macros,seed,episodes,eval_['initial_cost'],train['best_cost'],eval_['cost'],eval_['wirelength'],train['train_runtime_sec'],eval_['runtime_sec'],resume_from,str(run_dir)])
PY
}

create_openroad_artifacts() {
  local run_dir="$1"
  mkdir -p "${run_dir}/openroad"

  "${PYTHON_BIN}" "${ROOT_DIR}/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py" \
    "${run_dir}/eval/alphachip_like_final.plc" \
    "${DATA_DIR}/netlist.pb.txt" \
    "${run_dir}/openroad/alphachip_like_final_raw.tcl"

  "${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py" \
    --in_tcl "${run_dir}/openroad/alphachip_like_final_raw.tcl" \
    --out_tcl "${run_dir}/openroad/alphachip_like_final_openroad.tcl" \
    --mode place_macro \
    --escape_brackets

  if [[ "${PLATFORM}" == "NanGate45" && "${TESTCASE}" == "ariane133" ]]; then
    cat >"${run_dir}/openroad/view_alphachip_like_final.tcl" <<EOF
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.macro.lef
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/fakeram45_256x16.lef
read_def ${ROOT_DIR}/MacroPlacement/Flows/NanGate45/ariane133/def/Util_51/ariane133_fp_placed_macros.def
source ${run_dir}/openroad/alphachip_like_final_openroad.tcl
gui::fit
EOF
  fi
}

run_one() {
  local mode="$1" stage="$2" macros="$3" resume_from="$4"
  local run_id="${EXPERIMENT_ID}_${mode}_stage${stage}_macros${macros}_seed${SEED}"
  local run_dir="${RESULT_ROOT}/${run_id}"
  mkdir -p "${run_dir}/train" "${run_dir}/eval" "${run_dir}/openroad"
  local train_args=(
    --netlist "${DATA_DIR}/netlist.pb.txt"
    --init_plc "${DATA_DIR}/initial.plc"
    --out_dir "${run_dir}/train"
    --episodes "${EPISODES_PER_STAGE}"
    --max_macros "${macros}"
    --seed "${SEED}"
    --stage_name "${mode}_stage${stage}_macros${macros}"
  )
  if [[ -n "${resume_from}" ]]; then
    train_args+=(--resume_from "${resume_from}")
  fi
  "${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py" "${train_args[@]}"
  "${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/evaluate_alphachip_like_policy.py" \
    --model "${run_dir}/train/alphachip_like_actor_critic.pt" \
    --netlist "${DATA_DIR}/netlist.pb.txt" \
    --init_plc "${DATA_DIR}/initial.plc" \
    --out_dir "${run_dir}/eval" \
    --max_macros "${macros}" \
    --deterministic
  create_openroad_artifacts "${run_dir}"
  append_row "${run_id}" "${mode}" "${stage}" "${macros}" "${EPISODES_PER_STAGE}" "${run_dir}" "${resume_from}"
  printf '%s\n' "${run_dir}/train/alphachip_like_actor_critic.pt"
}

previous_ckpt=""
stage_num=1
for macros in "${STAGES[@]}"; do
  previous_ckpt="$(run_one curriculum "${stage_num}" "${macros}" "${previous_ckpt}" | tail -n1)"
  stage_num=$((stage_num + 1))
done

final_stage="${STAGES[${#STAGES[@]}-1]}"
run_one scratch final "${final_stage}" "" >/dev/null

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/render_curriculum_table.py" "${TABLE_CSV}"
