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

CONFIG_PATH="${DESIGN_CONFIG#designs/}"
PLATFORM="${CONFIG_PATH%%/*}"
DESIGN_PATH="${CONFIG_PATH#*/}"
DESIGN="${DESIGN_PATH%%/*}"

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

if [ "${CONFIG_PATH}" = "${DESIGN_CONFIG}" ] || [ -z "${PLATFORM}" ] || [ -z "${DESIGN}" ]; then
  echo "Expected config path: designs/<platform>/<design>/config.mk"
  exit 2
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
  -e ARCHIVE_PLATFORM="${PLATFORM}" \
  -e ARCHIVE_DESIGN="${DESIGN}" \
  -w /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow \
  "${CONTAINER_NAME}" \
  bash -lc '
    set -euo pipefail

    export_stage_results() {
      local prefix="$1"
      local output_root="$2"
      local source_dir="results/${ARCHIVE_PLATFORM}/${ARCHIVE_DESIGN}/${FLOW_VARIANT}"
      local output_dir="${output_root}/${ARCHIVE_PLATFORM}/${ARCHIVE_DESIGN}/${FLOW_VARIANT}"

      rm -rf "${output_dir}"
      mkdir -p "${output_dir}"
      find "${source_dir}" -maxdepth 1 -type f -name "${prefix}_*" \
        -exec cp -f {} "${output_dir}/" \;
    }

    make -j"${JOBS}" \
      DESIGN_CONFIG="${DESIGN_CONFIG}" \
      FLOW_VARIANT="${FLOW_VARIANT}" \
      synth
    export_stage_results 1 SynthesisResults

    if [ "${STAGE}" = "floorplan" ] || [ "${STAGE}" = "place" ]; then
      make -j"${JOBS}" \
        DESIGN_CONFIG="${DESIGN_CONFIG}" \
        FLOW_VARIANT="${FLOW_VARIANT}" \
        do-floorplan
      export_stage_results 2 FloorplanningResults
    fi

    if [ "${STAGE}" = "place" ]; then
      make -j"${JOBS}" \
        DESIGN_CONFIG="${DESIGN_CONFIG}" \
        FLOW_VARIANT="${FLOW_VARIANT}" \
        do-place
      export_stage_results 3 PlacementResults
    fi
  '

echo
echo "Completed stage: ${STAGE}"
echo "ORFS working results: ${FLOW_DIR}/results/${PLATFORM}/${DESIGN}/${FLOW_VARIANT}/"
echo "Synthesis results  : ${FLOW_DIR}/SynthesisResults/${PLATFORM}/${DESIGN}/${FLOW_VARIANT}/"
if [ "${STAGE}" = "floorplan" ] || [ "${STAGE}" = "place" ]; then
  echo "Floorplan results  : ${FLOW_DIR}/FloorplanningResults/${PLATFORM}/${DESIGN}/${FLOW_VARIANT}/"
fi
if [ "${STAGE}" = "place" ]; then
  echo "Placement results  : ${FLOW_DIR}/PlacementResults/${PLATFORM}/${DESIGN}/${FLOW_VARIANT}/"
fi
