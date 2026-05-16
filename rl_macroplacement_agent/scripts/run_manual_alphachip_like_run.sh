#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/rl_env/bin/python}"

usage() {
  cat <<'EOF'
Usage:
  run_manual_alphachip_like_run.sh PLATFORM TESTCASE RUN_NUMBER EPISODES MACROS SEED [RESUME_FROM]

Example:
  bash rl_macroplacement_agent/scripts/run_manual_alphachip_like_run.sh \
    NanGate45 ariane133 ac001 205 5 1
EOF
}

if [[ $# -lt 6 || $# -gt 7 ]]; then
  usage
  exit 2
fi

PLATFORM="$1"
TESTCASE="$2"
RUN_NUMBER="$3"
EPISODES="$4"
MACROS="$5"
SEED="$6"
RESUME_FROM="${7:-}"
STEPS=$((EPISODES * MACROS))
RUN_ID="run_${RUN_NUMBER}_alphachip_like_episodes${EPISODES}_macros${MACROS}_seed${SEED}"

DATA_DIR="${ROOT_DIR}/MacroPlacement/Flows/${PLATFORM}/${TESTCASE}/netlist/output_CT_Grouping"
RESULT_ROOT="${ROOT_DIR}/rl_macroplacement_agent/results/manual_runs/${PLATFORM}/${TESTCASE}"
RUN_DIR="${RESULT_ROOT}/${RUN_ID}"
TABLE_DIR="${RESULT_ROOT}/tables"
TABLE_CSV="${TABLE_DIR}/run_table.csv"

mkdir -p "${RUN_DIR}/train" "${RUN_DIR}/eval" "${RUN_DIR}/openroad" "${TABLE_DIR}"

cat >"${RUN_DIR}/run_info.txt" <<EOF
agent=AlphaChipLikePPO
platform=${PLATFORM}
testcase=${TESTCASE}
steps=${STEPS}
episodes=${EPISODES}
macros=${MACROS}
seed=${SEED}
resume_from=${RESUME_FROM}
data_dir=${DATA_DIR}
EOF

echo "[1/5] Training ${RUN_ID}"
TRAIN_ARGS=(
  --netlist "${DATA_DIR}/netlist.pb.txt" \
  --init_plc "${DATA_DIR}/initial.plc" \
  --out_dir "${RUN_DIR}/train" \
  --episodes "${EPISODES}" \
  --max_macros "${MACROS}" \
  --seed "${SEED}"
)
if [[ -n "${RESUME_FROM}" ]]; then
  TRAIN_ARGS+=(--resume_from "${RESUME_FROM}")
fi
"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py" \
  "${TRAIN_ARGS[@]}"

echo "[2/5] Evaluating ${RUN_ID}"
"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/evaluate_alphachip_like_policy.py" \
  --model "${RUN_DIR}/train/alphachip_like_actor_critic.pt" \
  --netlist "${DATA_DIR}/netlist.pb.txt" \
  --init_plc "${DATA_DIR}/initial.plc" \
  --out_dir "${RUN_DIR}/eval" \
  --max_macros "${MACROS}" \
  --deterministic

echo "[3/5] Creating OpenROAD Tcl artifacts"
"${PYTHON_BIN}" "${ROOT_DIR}/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py" \
  "${RUN_DIR}/eval/alphachip_like_final.plc" \
  "${DATA_DIR}/netlist.pb.txt" \
  "${RUN_DIR}/openroad/alphachip_like_final_raw.tcl"

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py" \
  --in_tcl "${RUN_DIR}/openroad/alphachip_like_final_raw.tcl" \
  --out_tcl "${RUN_DIR}/openroad/alphachip_like_final_openroad.tcl" \
  --mode place_macro \
  --escape_brackets

if [[ "${PLATFORM}" == "NanGate45" && "${TESTCASE}" == "ariane133" ]]; then
  cat >"${RUN_DIR}/openroad/view_alphachip_like_final.tcl" <<EOF
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.macro.lef
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/fakeram45_256x16.lef
read_def ${ROOT_DIR}/MacroPlacement/Flows/NanGate45/ariane133/def/Util_51/ariane133_fp_placed_macros.def
source ${RUN_DIR}/openroad/alphachip_like_final_openroad.tcl
gui::fit
EOF
fi

echo "[4/5] Appending shared CSV table row"
"${PYTHON_BIN}" - "${TABLE_CSV}" "${RUN_ID}" "${PLATFORM}" "${TESTCASE}" \
  "${STEPS}" "${EPISODES}" "${MACROS}" "${SEED}" "${RUN_DIR}" <<'PY'
import csv
import json
import sys
from pathlib import Path

table_path = Path(sys.argv[1])
run_id, platform, testcase = sys.argv[2:5]
steps, episodes, macros, seed = map(int, sys.argv[5:9])
run_dir = Path(sys.argv[9])
train = json.loads((run_dir / "train" / "alphachip_like_train_summary.json").read_text())
eval_ = json.loads((run_dir / "eval" / "alphachip_like_eval_summary.json").read_text())
fieldnames = [
    "run_id", "agent", "platform", "testcase", "steps", "episodes", "macros", "seed",
    "train_best_cost", "eval_cost", "eval_best_cost", "wirelength", "density_cost",
    "train_runtime_sec", "eval_runtime_sec", "run_dir",
]
rows = []
if table_path.exists():
    with table_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            migrated = {name: row.get(name, "") for name in fieldnames}
            if not migrated["agent"]:
                migrated["agent"] = "MaskablePPO"
            if not migrated["eval_runtime_sec"]:
                migrated["eval_runtime_sec"] = row.get("runtime_sec", "")
            rows.append(migrated)
rows = [row for row in rows if row["run_id"] != run_id]
rows.append({
    "run_id": run_id,
    "agent": "AlphaChipLikePPO",
    "platform": platform,
    "testcase": testcase,
    "steps": steps,
    "episodes": episodes,
    "macros": macros,
    "seed": seed,
    "train_best_cost": train["best_cost"],
    "eval_cost": eval_["cost"],
    "eval_best_cost": eval_["best_cost"],
    "wirelength": eval_["wirelength"],
    "density_cost": eval_["density_cost"],
    "train_runtime_sec": train["train_runtime_sec"],
    "eval_runtime_sec": eval_["runtime_sec"],
    "run_dir": str(run_dir),
})
with table_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
PY

echo "[5/5] Rendering Markdown table"
"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/render_manual_run_table.py" "${TABLE_CSV}"
echo "Completed: ${RUN_DIR}"
