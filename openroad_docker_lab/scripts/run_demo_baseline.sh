#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RL_IMAGE="${RL_IMAGE:-datn-openroad-rl:latest}"
RUN_PIPELINE="${RUN_PIPELINE:-0}"
FLOW_VARIANT="${FLOW_VARIANT:-macro_demo_run_01}"
RUN_NAME="${RUN_NAME:-macro_cluster_demo_orfs}"
EPISODES="${EPISODES:-100}"
ROLLOUT_EPISODES="${ROLLOUT_EPISODES:-4}"
MAX_MACROS="${MAX_MACROS:-4}"
MAX_NODES="${MAX_NODES:-2048}"
MAX_EDGES="${MAX_EDGES:-6000}"
MAX_GRID="${MAX_GRID:-32}"
BATCH_SIZE="${BATCH_SIZE:-64}"
DEVICE="${DEVICE:-cpu}"
EXPERIMENT_TAG="${EXPERIMENT_TAG:-baseline_v1}"
SEEDS="${SEEDS:-1 2 3}"

DATASET_DIR="${ROOT_DIR}/MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}"
NETLIST_PATH="${DATASET_DIR}/macro_cluster_demo.pb.txt"
PLC_PATH="${DATASET_DIR}/macro_cluster_demo.plc"
RESULT_ROOT="${ROOT_DIR}/experiments/macro_cluster_demo/${EXPERIMENT_TAG}"

if [ "${RUN_PIPELINE}" = "1" ]; then
  "${ROOT_DIR}/openroad_docker_lab/scripts/run_demo_pipeline.sh"
fi

if [ ! -f "${NETLIST_PATH}" ] || [ ! -f "${PLC_PATH}" ]; then
  echo "Missing dataset files:"
  echo "  ${NETLIST_PATH}"
  echo "  ${PLC_PATH}"
  echo "Run the pipeline first:"
  echo "  ./openroad_docker_lab/scripts/run_demo_pipeline.sh"
  exit 1
fi

if ! docker image inspect "${RL_IMAGE}" >/dev/null 2>&1; then
  echo "Missing RL image: ${RL_IMAGE}"
  echo "Build it first with: ./datn_docker_env/scripts/build.sh"
  exit 1
fi

mkdir -p "${RESULT_ROOT}"

echo "Dataset:"
echo "  ${NETLIST_PATH}"
echo "  ${PLC_PATH}"
echo "Experiment root:"
echo "  ${RESULT_ROOT}"
echo "Seeds: ${SEEDS}"
echo

for seed in ${SEEDS}; do
  OUT_DIR="/workspace/DATN/experiments/macro_cluster_demo/${EXPERIMENT_TAG}/seed_${seed}"
  HOST_OUT_DIR="${RESULT_ROOT}/seed_${seed}"
  mkdir -p "${HOST_OUT_DIR}"

  echo "=== Running seed ${seed} ==="
  docker run --rm \
    -v "${ROOT_DIR}:/workspace/DATN" \
    -w /workspace/DATN \
    "${RL_IMAGE}" \
    bash -lc "
      set -euo pipefail
      python3 rl_macroplacement_agent/scripts/train_ppo.py \
        --netlist 'MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.pb.txt' \
        --init_plc 'MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.plc' \
        --out_dir '${OUT_DIR}' \
        --episodes '${EPISODES}' \
        --rollout_episodes '${ROLLOUT_EPISODES}' \
        --max_macros '${MAX_MACROS}' \
        --max_nodes '${MAX_NODES}' \
        --max_edges '${MAX_EDGES}' \
        --max_grid '${MAX_GRID}' \
        --batch_size '${BATCH_SIZE}' \
        --seed '${seed}' \
        --device '${DEVICE}'
    " | tee "${HOST_OUT_DIR}/train.log"
done

python3 "${ROOT_DIR}/openroad_docker_lab/scripts/summarize_demo.py" \
  --root "${RESULT_ROOT}" \
  --output "${RESULT_ROOT}/summary.csv"

echo
echo "Baseline runs completed."
echo "Summary:"
echo "  ${RESULT_ROOT}/summary.csv"
