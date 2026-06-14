#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "${LAB_DIR}/.." && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"
JOBS="${JOBS:-1}"
FLOW_VARIANT="${FLOW_VARIANT:-datn}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "Docker image not found: ${IMAGE_NAME}"
  echo "Build it with ./openroad_docker_lab/scripts/build.sh"
  exit 1
fi

if ! docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
  echo "Creating container ${CONTAINER_NAME}..."
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}:/workspace/DATN" \
    -w /workspace/DATN \
    "${IMAGE_NAME}" \
    sleep infinity >/dev/null
fi

if [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}")" != "true" ]; then
  docker start "${CONTAINER_NAME}" >/dev/null
fi

echo "[1/4] Checking Yosys and OpenROAD"
docker exec "${CONTAINER_NAME}" bash -lc '
  /opt/oss-cad-suite/bin/yosys -V
  /usr/local/bin/openroad -version
'

echo "[2/4] Running Ariane133 synthesis, floorplanning, and placement"
docker exec \
  -e PATH="/opt/oss-cad-suite/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  -e YOSYS_EXE="/opt/oss-cad-suite/bin/yosys" \
  -e OPENROAD_EXE="/usr/local/bin/openroad" \
  -e JOBS="${JOBS}" \
  -e FLOW_VARIANT="${FLOW_VARIANT}" \
  -w /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow \
  "${CONTAINER_NAME}" \
  bash -lc '
    set -euo pipefail
    make -j"${JOBS}" \
      DESIGN_CONFIG=designs/nangate45/ariane133/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      synth
    make -j"${JOBS}" \
      DESIGN_CONFIG=designs/nangate45/ariane133/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      do-floorplan
    make -j"${JOBS}" \
      DESIGN_CONFIG=designs/nangate45/ariane133/config.mk \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      do-place
  '

echo "[3/4] Exporting DEF from the placed ODB"
docker exec \
  -w /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow \
  -e FLOW_VARIANT="${FLOW_VARIANT}" \
  "${CONTAINER_NAME}" \
  bash -lc '
    set -euo pipefail
    result_dir="results/nangate45/ariane133/${FLOW_VARIANT}"
    mkdir -p "$result_dir"
    cat > /tmp/export_ariane133_def.tcl <<EOF
read_db $result_dir/3_place.odb
write_def $result_dir/3_place.def
exit
EOF
    /usr/local/bin/openroad /tmp/export_ariane133_def.tcl
  '

RESULT_DIR="${PROJECT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow/results/nangate45/ariane133/${FLOW_VARIANT}"
echo "[4/4] Verifying output files"
for output in 1_synth.odb 2_floorplan.odb 3_place.odb 3_place.def; do
  if [ ! -s "${RESULT_DIR}/${output}" ]; then
    echo "Missing output: ${RESULT_DIR}/${output}"
    exit 1
  fi
  ls -lh "${RESULT_DIR}/${output}"
done

cat <<EOF

OpenROAD flow completed.
Results: ${RESULT_DIR}

The legacy TILOS CodeElements flow requires the OpenROAD 'partition_design'
command, which is unavailable in the current build. Use the existing Ariane133
benchmark files for RL training:
  MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
  MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
EOF
