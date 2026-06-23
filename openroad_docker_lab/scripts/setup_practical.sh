#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FLOW_DIR="${ROOT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow"
SRC_FILE="${ROOT_DIR}/example/practical_macro_soc.v"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"

if [ ! -f "${SRC_FILE}" ]; then
  echo "Missing RTL source: ${SRC_FILE}"
  exit 1
fi

ensure_container() {
  if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo "Docker image not found: ${IMAGE_NAME}"
    echo "Build it first with ./openroad_docker_lab/scripts/build.sh"
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
}

ensure_container

docker cp "${SRC_FILE}" "${CONTAINER_NAME}:/tmp/practical_macro_soc.v"

docker exec "${CONTAINER_NAME}" bash -lc '
  set -euo pipefail
  mkdir -p /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/src/practical_macro_soc
  mkdir -p /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/practical_macro_soc

  cp /tmp/practical_macro_soc.v \
    /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/src/practical_macro_soc/practical_macro_soc.v

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/practical_macro_soc/config.mk <<'"'"'EOF'"'"'
export DESIGN_NAME = practical_macro_soc
export DESIGN_NICKNAME = practical_macro_soc
export PLATFORM = nangate45

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/practical_macro_soc.v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc
export IO_CONSTRAINTS = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/io.tcl
export MACRO_PLACEMENT_TCL = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/macro_placement.tcl

export ADDITIONAL_LEFS = $(PLATFORM_DIR)/lef/fakeram45_256x16.lef
export ADDITIONAL_LIBS = $(PLATFORM_DIR)/lib/fakeram45_256x16.lib
export PRESERVE_CELLS = fakeram45_256x16

export DIE_AREA = 0 0 800 800
export CORE_AREA = 40 40 760 760

export PLACE_DENSITY = 0.50
export MACRO_PLACE_HALO = 5 5
export RTLMP_MIN_AR = 0.05
export ABC_AREA = 1
EOF

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/practical_macro_soc/constraint.sdc <<'"'"'EOF'"'"'
create_clock -name core_clock -period 10.0 [get_ports clk]
set_input_delay 0.2 -clock core_clock [get_ports rst_n]
set_input_delay 0.2 -clock core_clock [get_ports start]
set_input_delay 0.2 -clock core_clock [get_ports irq_i]
set_output_delay 0.2 -clock core_clock [get_ports status_o*]
EOF

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/practical_macro_soc/io.tcl <<'"'"'EOF'"'"'
place_pins \
  -hor_layers metal5 \
  -ver_layers metal6 \
  -exclude top:* \
  -exclude bottom:*
EOF

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/practical_macro_soc/macro_placement.tcl <<'"'"'EOF'"'"'
place_macro -macro_name u_instr_mem0 -location {80 620} -orientation R0
place_macro -macro_name u_instr_mem1 -location {180 620} -orientation R0

place_macro -macro_name u_data_mem0 -location {80 520} -orientation R0
place_macro -macro_name u_data_mem1 -location {180 520} -orientation R0

place_macro -macro_name u_dma_mem0 -location {500 620} -orientation R0
place_macro -macro_name u_dma_mem1 -location {600 620} -orientation R0

place_macro -macro_name u_io_mem0 -location {500 520} -orientation R0
place_macro -macro_name u_io_mem1 -location {600 520} -orientation R0
EOF
'

echo "Installed practical_macro_soc into ORFS:"
echo "  ${FLOW_DIR}/designs/src/practical_macro_soc/practical_macro_soc.v"
echo "  ${FLOW_DIR}/designs/nangate45/practical_macro_soc/config.mk"
echo "  ${FLOW_DIR}/designs/nangate45/practical_macro_soc/constraint.sdc"
echo "  ${FLOW_DIR}/designs/nangate45/practical_macro_soc/io.tcl"
echo "  ${FLOW_DIR}/designs/nangate45/practical_macro_soc/macro_placement.tcl"
