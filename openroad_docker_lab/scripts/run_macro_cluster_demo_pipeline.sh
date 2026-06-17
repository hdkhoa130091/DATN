#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENROAD_IMAGE="${OPENROAD_IMAGE:-openroad-docker-lab:latest}"
OPENROAD_CONTAINER="${OPENROAD_CONTAINER:-openroad_cli}"
RL_IMAGE="${RL_IMAGE:-datn-openroad-rl:latest}"
FLOW_VARIANT="${FLOW_VARIANT:-macro_demo_run_01}"
RUN_NAME="${RUN_NAME:-macro_cluster_demo_orfs}"
RUN_RL="${RUN_RL:-0}"
RL_OUT_DIR="${RL_OUT_DIR:-/workspace/DATN/tmp_rl_macro_cluster_demo}"

ensure_openroad_container() {
  if ! docker image inspect "${OPENROAD_IMAGE}" >/dev/null 2>&1; then
    echo "Missing Docker image: ${OPENROAD_IMAGE}"
    echo "Build it first with: ./openroad_docker_lab/scripts/build.sh"
    exit 1
  fi

  if ! docker container inspect "${OPENROAD_CONTAINER}" >/dev/null 2>&1; then
    docker run -d \
      --name "${OPENROAD_CONTAINER}" \
      -v "${ROOT_DIR}:/workspace/DATN" \
      -w /workspace/DATN \
      "${OPENROAD_IMAGE}" \
      sleep infinity >/dev/null
  elif [ "$(docker inspect -f '{{.State.Running}}' "${OPENROAD_CONTAINER}")" != "true" ]; then
    docker start "${OPENROAD_CONTAINER}" >/dev/null
  fi
}

ensure_hmetis_runtime() {
  docker exec "${OPENROAD_CONTAINER}" bash -lc '
    set -euo pipefail
    if [ -e /lib/ld-linux.so.2 ] && [ -e /lib32/libstdc++.so.6 ]; then
      exit 0
    fi
    dpkg --add-architecture i386
    apt-get update
    apt-get install -y libc6:i386 libstdc++6:i386
  '
}

run_in_openroad() {
  docker exec \
    -e PATH="/opt/oss-cad-suite/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    -e YOSYS_EXE="/opt/oss-cad-suite/bin/yosys" \
    -e OPENROAD_EXE="/usr/local/bin/openroad" \
    -w /workspace/DATN \
    "${OPENROAD_CONTAINER}" \
    bash -lc "$1"
}

echo "[1/7] Ensuring OpenROAD container is available"
ensure_openroad_container

echo "[2/7] Installing macro_cluster_demo into ORFS"
run_in_openroad "./openroad_docker_lab/scripts/setup_macro_cluster_demo.sh"

echo "[3/7] Running synthesis"
FLOW_VARIANT="${FLOW_VARIANT}" \
  "${ROOT_DIR}/openroad_docker_lab/scripts/run_orfs_design.sh" \
  designs/nangate45/macro_cluster_demo/config.mk synth

echo "[4/7] Running floorplan and placement"
"${ROOT_DIR}/openroad_docker_lab/scripts/manual_macro_cluster_demo_floorplan.sh" "${FLOW_VARIANT}"

echo "[5/7] Preparing flow.py input directory"
run_in_openroad "./openroad_docker_lab/scripts/prepare_flowpy_run_from_orfs.sh \
  nangate45 macro_cluster_demo '${FLOW_VARIANT}' '${RUN_NAME}'"

echo "[6/7] Running flow.py"
ensure_hmetis_runtime
run_in_openroad "python3 MacroPlacement/Flows/util/flow.py \
  MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME} \
  MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/output_CodeElement"

echo "[7/7] Validating generated dataset"
run_in_openroad "python3 rl_macroplacement_agent/scripts/inspect_dataset.py \
  --netlist MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.pb.txt \
  --initial_plc MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.plc"

if [ "${RUN_RL}" = "1" ]; then
  echo "[RL] Running PPO smoke test"
  if ! docker image inspect "${RL_IMAGE}" >/dev/null 2>&1; then
    echo "Missing RL image: ${RL_IMAGE}"
    echo "Build it first with: ./datn_docker_env/scripts/build.sh"
    exit 1
  fi

  docker run --rm \
    -v "${ROOT_DIR}:/workspace/DATN" \
    -w /workspace/DATN \
    "${RL_IMAGE}" \
    python3 rl_macroplacement_agent/scripts/train_alphachip_like_ppo.py \
      --netlist "MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.pb.txt" \
      --init_plc "MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.plc" \
      --out_dir "${RL_OUT_DIR}" \
      --episodes 1 \
      --rollout_episodes 1 \
      --max_macros 4 \
      --max_nodes 2048 \
      --max_edges 6000 \
      --max_grid 32 \
      --batch_size 1 \
      --device cpu
fi

echo
echo "Pipeline completed."
echo "Generated dataset:"
echo "  ${ROOT_DIR}/MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.pb.txt"
echo "  ${ROOT_DIR}/MacroPlacement/Flows/NanGate45/generated/macro_cluster_demo/${RUN_NAME}/macro_cluster_demo.plc"
