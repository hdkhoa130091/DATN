#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/rl_env/bin/python}"

usage() {
  cat <<'EOF'
Usage:
  run_manual_ppo_run.sh PLATFORM TESTCASE RUN_NUMBER STEPS MACROS SEED

Example:
  bash rl_macroplacement_agent/scripts/run_manual_ppo_run.sh \
    NanGate45 ariane133 001 1000 5 1
EOF
}

if [[ $# -ne 6 ]]; then
  usage
  exit 2
fi

PLATFORM="$1"
TESTCASE="$2"
RUN_NUMBER="$3"
STEPS="$4"
MACROS="$5"
SEED="$6"
RUN_ID="run_${RUN_NUMBER}_steps${STEPS}_macros${MACROS}_seed${SEED}"

DATA_DIR="${ROOT_DIR}/MacroPlacement/Flows/${PLATFORM}/${TESTCASE}/netlist/output_CT_Grouping"
RESULT_ROOT="${ROOT_DIR}/rl_macroplacement_agent/results/manual_runs/${PLATFORM}/${TESTCASE}"
RUN_DIR="${RESULT_ROOT}/${RUN_ID}"
TABLE_DIR="${RESULT_ROOT}/tables"
TABLE_CSV="${TABLE_DIR}/run_table.csv"

for required in "${DATA_DIR}/netlist.pb.txt" "${DATA_DIR}/initial.plc"; do
  if [[ ! -f "${required}" ]]; then
    echo "Missing required input: ${required}" >&2
    exit 2
  fi
done

mkdir -p "${RUN_DIR}/train" "${RUN_DIR}/eval" "${RUN_DIR}/openroad" "${TABLE_DIR}"

cat >"${RUN_DIR}/run_info.txt" <<EOF
platform=${PLATFORM}
testcase=${TESTCASE}
steps=${STEPS}
macros=${MACROS}
seed=${SEED}
data_dir=${DATA_DIR}
EOF

echo "[1/5] Training ${RUN_ID}"
"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/train_maskable_ppo.py" \
  --netlist "${DATA_DIR}/netlist.pb.txt" \
  --init_plc "${DATA_DIR}/initial.plc" \
  --out_dir "${RUN_DIR}/train" \
  --steps "${STEPS}" \
  --max_macros "${MACROS}" \
  --seed "${SEED}" \
  --n_steps 128 \
  --batch_size 64

echo "[2/5] Evaluating ${RUN_ID}"
"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/evaluate_policy.py" \
  --model "${RUN_DIR}/train/maskable_ppo_model.zip" \
  --netlist "${DATA_DIR}/netlist.pb.txt" \
  --init_plc "${DATA_DIR}/initial.plc" \
  --out_dir "${RUN_DIR}/eval" \
  --max_macros "${MACROS}" \
  --deterministic

echo "[3/5] Creating OpenROAD Tcl artifacts"
"${PYTHON_BIN}" "${ROOT_DIR}/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py" \
  "${RUN_DIR}/train/best_rl.plc" \
  "${DATA_DIR}/netlist.pb.txt" \
  "${RUN_DIR}/openroad/best_rl_raw.tcl"

"${PYTHON_BIN}" "${ROOT_DIR}/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py" \
  "${RUN_DIR}/eval/ppo_final.plc" \
  "${DATA_DIR}/netlist.pb.txt" \
  "${RUN_DIR}/openroad/ppo_final_raw.tcl"

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py" \
  --in_tcl "${RUN_DIR}/openroad/best_rl_raw.tcl" \
  --out_tcl "${RUN_DIR}/openroad/best_rl_openroad.tcl" \
  --mode place_macro \
  --escape_brackets

"${PYTHON_BIN}" "${ROOT_DIR}/rl_macroplacement_agent/scripts/plc_to_openroad_tcl.py" \
  --in_tcl "${RUN_DIR}/openroad/ppo_final_raw.tcl" \
  --out_tcl "${RUN_DIR}/openroad/ppo_final_openroad.tcl" \
  --mode place_macro \
  --escape_brackets

if [[ "${PLATFORM}" == "NanGate45" && "${TESTCASE}" == "ariane133" ]]; then
  for view in best_rl ppo_final; do
    cat >"${RUN_DIR}/openroad/view_${view}.tcl" <<EOF
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.macro.lef
read_lef ${ROOT_DIR}/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/fakeram45_256x16.lef
read_def ${ROOT_DIR}/MacroPlacement/Flows/NanGate45/ariane133/def/Util_51/ariane133_fp_placed_macros.def
source ${RUN_DIR}/openroad/${view}_openroad.tcl
gui::fit
EOF
  done
fi

echo "[4/5] Appending CSV table row"
"${PYTHON_BIN}" - "${TABLE_CSV}" "${RUN_ID}" "${PLATFORM}" "${TESTCASE}" \
  "${STEPS}" "${MACROS}" "${SEED}" "${RUN_DIR}" <<'PY'
import csv
import json
import sys
from pathlib import Path

table_path = Path(sys.argv[1])
run_id, platform, testcase = sys.argv[2:5]
steps, macros, seed = map(int, sys.argv[5:8])
run_dir = Path(sys.argv[8])

train = json.loads((run_dir / "train" / "train_summary.json").read_text())
eval_ = json.loads((run_dir / "eval" / "ppo_eval_summary.json").read_text())

fieldnames = [
    "run_id",
    "platform",
    "testcase",
    "steps",
    "macros",
    "seed",
    "train_best_cost",
    "eval_cost",
    "eval_best_cost",
    "wirelength",
    "density_cost",
    "runtime_sec",
    "run_dir",
]
rows = []
if table_path.exists():
    with table_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
rows = [row for row in rows if row["run_id"] != run_id]
rows.append(
    {
        "run_id": run_id,
        "platform": platform,
        "testcase": testcase,
        "steps": steps,
        "macros": macros,
        "seed": seed,
        "train_best_cost": train["best_cost"],
        "eval_cost": eval_["cost"],
        "eval_best_cost": eval_["best_cost"],
        "wirelength": eval_["wirelength"],
        "density_cost": eval_["density_cost"],
        "runtime_sec": eval_["runtime_sec"],
        "run_dir": str(run_dir),
    }
)
with table_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
PY

echo "[5/5] Rendering Markdown table"
"${PYTHON_BIN}" - "${TABLE_CSV}" <<'PY'
import csv
import sys
from pathlib import Path

csv_path = Path(sys.argv[1])
md_path = csv_path.with_suffix(".md")
rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
headers = [
    "run_id",
    "steps",
    "macros",
    "seed",
    "train_best_cost",
    "eval_cost",
    "eval_best_cost",
    "wirelength",
    "density_cost",
    "runtime_sec",
]
lines = [
    "| " + " | ".join(headers) + " |",
    "|" + "|".join(["---"] * len(headers)) + "|",
]
for row in rows:
    lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(md_path.read_text(encoding="utf-8"))
PY

echo "Completed: ${RUN_DIR}"
echo "OpenROAD Tcl:"
echo "  ${RUN_DIR}/openroad/best_rl_openroad.tcl"
echo "  ${RUN_DIR}/openroad/ppo_final_openroad.tcl"
