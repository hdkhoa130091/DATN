#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DIR="$(cd "${LAB_DIR}/.." && pwd)"
FLOW_DIR="${PROJECT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"
DESIGN_CONFIG="${1:-}"
STAGE="${2:-synth}"
FLOW_VARIANT="${FLOW_VARIANT:-datn}"
JOBS="${JOBS:-1}"

usage() {
  cat <<EOF
Usage:
  $0 <config.mk relative to ORFS flow> [synth|floorplan|place]

Examples:
  $0 designs/nangate45/gcd/config.mk synth
  $0 designs/nangate45/adder8/config.mk place
EOF
}

if [ -z "${DESIGN_CONFIG}" ]; then
  usage
  exit 2
fi

case "${STAGE}" in
  synth|floorplan|place) ;;
  *)
    echo "Invalid stage: ${STAGE}"
    usage
    exit 2
    ;;
esac

if [ ! -s "${FLOW_DIR}/${DESIGN_CONFIG}" ]; then
  echo "Design configuration not found: ${FLOW_DIR}/${DESIGN_CONFIG}"
  exit 1
fi

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "Docker image not found: ${IMAGE_NAME}"
  echo "Build it with ./openroad_docker_lab/scripts/build.sh"
  exit 1
fi

if ! docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}:/workspace/DATN" \
    -w /workspace/DATN \
    "${IMAGE_NAME}" \
    sleep infinity >/dev/null
elif [ "$(docker inspect -f '{{.State.Running}}' "${CONTAINER_NAME}")" != "true" ]; then
  docker start "${CONTAINER_NAME}" >/dev/null
fi

echo "Config : ${DESIGN_CONFIG}"
echo "Stage  : ${STAGE}"
echo "Variant: ${FLOW_VARIANT}"

docker exec \
  -e PATH="/opt/oss-cad-suite/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  -e YOSYS_EXE="/opt/oss-cad-suite/bin/yosys" \
  -e OPENROAD_EXE="/usr/local/bin/openroad" \
  -e DESIGN_CONFIG="${DESIGN_CONFIG}" \
  -e STAGE="${STAGE}" \
  -e FLOW_VARIANT="${FLOW_VARIANT}" \
  -e JOBS="${JOBS}" \
  -w /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow \
  "${CONTAINER_NAME}" \
  bash -lc '
    set -euo pipefail

    make -j"${JOBS}" \
      DESIGN_CONFIG="${DESIGN_CONFIG}" \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      synth

    if [ "${STAGE}" = "floorplan" ] || [ "${STAGE}" = "place" ]; then
      make -j"${JOBS}" \
        DESIGN_CONFIG="${DESIGN_CONFIG}" \
        FLOW_VARIANT="${FLOW_VARIANT}" \
        do-floorplan
    fi

    if [ "${STAGE}" = "place" ]; then
      make -j"${JOBS}" \
        DESIGN_CONFIG="${DESIGN_CONFIG}" \
        FLOW_VARIANT="${FLOW_VARIANT}" \
        do-place
    fi
  '

echo
echo "Completed stage: ${STAGE}"
echo "Results: ${FLOW_DIR}/results/<platform>/<design>/${FLOW_VARIANT}/"
