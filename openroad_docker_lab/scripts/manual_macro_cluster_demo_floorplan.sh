#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FLOW_DIR="${ROOT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"
FLOW_VARIANT="${1:-macro_demo_run_01}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "Docker image not found: ${IMAGE_NAME}"
  exit 1
fi

if ! docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -v "${ROOT_DIR}:/workspace/DATN" \
    -w /workspace/DATN \
    "${IMAGE_NAME}" \
    sleep infinity >/dev/null
elif [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}")" != "true" ]; then
  docker start "${CONTAINER_NAME}" >/dev/null
fi

docker exec \
  -e FLOW_VARIANT="${FLOW_VARIANT}" \
  -w /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow \
  "${CONTAINER_NAME}" \
  bash -lc '
    set -euo pipefail

    RESULTS_DIR="results/nangate45/macro_cluster_demo/${FLOW_VARIANT}"
    if [ ! -f "${RESULTS_DIR}/2_1_floorplan.odb" ]; then
      echo "Missing ${RESULTS_DIR}/2_1_floorplan.odb"
      exit 1
    fi

    cat > /tmp/manual_macro_cluster_demo_floorplan.tcl <<'"'"'EOF'"'"'
read_liberty ./platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib
read_liberty ./platforms/nangate45/lib/fakeram45_256x16.lib
read_db ./results/nangate45/macro_cluster_demo/$::env(FLOW_VARIANT)/2_1_floorplan.odb
read_sdc ./results/nangate45/macro_cluster_demo/$::env(FLOW_VARIANT)/2_1_floorplan.sdc
source ./platforms/nangate45/setRC.tcl

place_macro -macro_name u_mem0 -location {40.0 60.0} -orientation R0
place_macro -macro_name u_mem1 -location {140.0 60.0} -orientation R0
place_macro -macro_name u_mem2 -location {40.0 140.0} -orientation R0
place_macro -macro_name u_mem3 -location {140.0 140.0} -orientation R0

write_macro_placement ./results/nangate45/macro_cluster_demo/$::env(FLOW_VARIANT)/2_2_floorplan_macro.tcl
write_db ./results/nangate45/macro_cluster_demo/$::env(FLOW_VARIANT)/2_2_floorplan_macro.odb
exit
EOF

    openroad -exit /tmp/manual_macro_cluster_demo_floorplan.tcl

    make -j1 \
      DESIGN_CONFIG=designs/nangate45/macro_cluster_demo/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      do-2_3_floorplan_tapcell

    make -j1 \
      DESIGN_CONFIG=designs/nangate45/macro_cluster_demo/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      do-2_4_floorplan_pdn

    make -j1 \
      DESIGN_CONFIG=designs/nangate45/macro_cluster_demo/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      do-2_floorplan

    cp "results/nangate45/macro_cluster_demo/${FLOW_VARIANT}/2_1_floorplan.sdc" \
       "results/nangate45/macro_cluster_demo/${FLOW_VARIANT}/2_floorplan.sdc"

    make -j1 \
      DESIGN_CONFIG=designs/nangate45/macro_cluster_demo/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      do-place
  '
