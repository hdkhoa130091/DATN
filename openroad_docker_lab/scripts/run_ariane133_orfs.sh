#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "${LAB_DIR}/.." && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"
JOBS="${JOBS:-1}"
FLOW_VARIANT="${FLOW_VARIANT:-datn}"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "Khong tim thay image ${IMAGE_NAME}. Chay ./openroad_docker_lab/scripts/build.sh truoc."
  exit 1
fi

if ! docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
  echo "Tao container ${CONTAINER_NAME}..."
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

echo "[1/4] Kiem tra Yosys va OpenROAD"
docker exec "${CONTAINER_NAME}" bash -lc '
  /opt/oss-cad-suite/bin/yosys -V
  /usr/local/bin/openroad -version
'

echo "[2/4] Chay synthesis, floorplan va placement cho Ariane133"
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

echo "[3/4] Xuat DEF tu ODB placement"
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
echo "[4/4] Kiem tra ket qua"
for output in 1_synth.odb 2_floorplan.odb 3_place.odb 3_place.def; do
  if [ ! -s "${RESULT_DIR}/${output}" ]; then
    echo "Thieu ket qua: ${RESULT_DIR}/${output}"
    exit 1
  fi
  ls -lh "${RESULT_DIR}/${output}"
done

cat <<EOF

OpenROAD da hoan thanh.
Ket qua: ${RESULT_DIR}

Luu y: CodeElements TILOS cu dung lenh 'partition_design', lenh nay khong
con trong OpenROAD moi. De train RL ngay, dung bo benchmark da co:
  MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
  MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
EOF
