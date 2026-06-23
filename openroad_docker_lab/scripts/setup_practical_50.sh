#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FLOW_DIR="${ROOT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow"
SRC_FILE="${ROOT_DIR}/example/practical_macro_soc_50.v"
CONTAINER_NAME="${CONTAINER_NAME:-openroad_cli}"
IMAGE_NAME="${IMAGE_NAME:-openroad-docker-lab:latest}"
DESIGN_NAME="practical_macro_soc_50"

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

docker cp "${SRC_FILE}" "${CONTAINER_NAME}:/tmp/${DESIGN_NAME}.v"

docker exec "${CONTAINER_NAME}" bash -lc '
  set -euo pipefail
  mkdir -p /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/src/'"${DESIGN_NAME}"'
  mkdir -p /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/'"${DESIGN_NAME}"'

  cp /tmp/'"${DESIGN_NAME}"'.v \
    /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/src/'"${DESIGN_NAME}"'/'"${DESIGN_NAME}"'.v

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/'"${DESIGN_NAME}"'/config.mk <<'"'"'EOF'"'"'
export DESIGN_NAME = practical_macro_soc_50
export DESIGN_NICKNAME = practical_macro_soc_50
export PLATFORM = nangate45

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/practical_macro_soc_50.v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc
export IO_CONSTRAINTS = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/io.tcl
export MACRO_PLACEMENT_TCL = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/macro_placement.tcl

export ADDITIONAL_LEFS = $(PLATFORM_DIR)/lef/fakeram45_256x16.lef
export ADDITIONAL_LIBS = $(PLATFORM_DIR)/lib/fakeram45_256x16.lib
export PRESERVE_CELLS = fakeram45_256x16

export DIE_AREA = 0 0 900 900
export CORE_AREA = 40 40 860 860

export PLACE_DENSITY = 0.55
export MACRO_PLACE_HALO = 5 5
export RTLMP_MIN_AR = 0.05
export ABC_AREA = 1
EOF

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/'"${DESIGN_NAME}"'/constraint.sdc <<'"'"'EOF'"'"'
create_clock -name core_clock -period 10.0 [get_ports clk]
set_input_delay 0.2 -clock core_clock [get_ports rst_n]
set_input_delay 0.2 -clock core_clock [get_ports start]
set_input_delay 0.2 -clock core_clock [get_ports irq_i]
set_output_delay 0.2 -clock core_clock [get_ports status_o*]
EOF

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/'"${DESIGN_NAME}"'/io.tcl <<'"'"'EOF'"'"'
place_pins \
  -hor_layers metal5 \
  -ver_layers metal6 \
  -exclude top:* \
  -exclude bottom:*
EOF

  cat > /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow/designs/nangate45/'"${DESIGN_NAME}"'/macro_placement.tcl <<'"'"'EOF'"'"'
place_macro -macro_name gen_mem[0].u_mem -location {60 720} -orientation R0
place_macro -macro_name gen_mem[1].u_mem -location {150 720} -orientation R0
place_macro -macro_name gen_mem[2].u_mem -location {240 720} -orientation R0
place_macro -macro_name gen_mem[3].u_mem -location {330 720} -orientation R0
place_macro -macro_name gen_mem[4].u_mem -location {420 720} -orientation R0
place_macro -macro_name gen_mem[5].u_mem -location {510 720} -orientation R0
place_macro -macro_name gen_mem[6].u_mem -location {600 720} -orientation R0
place_macro -macro_name gen_mem[7].u_mem -location {690 720} -orientation R0

place_macro -macro_name gen_mem[8].u_mem -location {60 650} -orientation R0
place_macro -macro_name gen_mem[9].u_mem -location {150 650} -orientation R0
place_macro -macro_name gen_mem[10].u_mem -location {240 650} -orientation R0
place_macro -macro_name gen_mem[11].u_mem -location {330 650} -orientation R0
place_macro -macro_name gen_mem[12].u_mem -location {420 650} -orientation R0
place_macro -macro_name gen_mem[13].u_mem -location {510 650} -orientation R0
place_macro -macro_name gen_mem[14].u_mem -location {600 650} -orientation R0
place_macro -macro_name gen_mem[15].u_mem -location {690 650} -orientation R0

place_macro -macro_name gen_mem[16].u_mem -location {60 580} -orientation R0
place_macro -macro_name gen_mem[17].u_mem -location {150 580} -orientation R0
place_macro -macro_name gen_mem[18].u_mem -location {240 580} -orientation R0
place_macro -macro_name gen_mem[19].u_mem -location {330 580} -orientation R0
place_macro -macro_name gen_mem[20].u_mem -location {420 580} -orientation R0
place_macro -macro_name gen_mem[21].u_mem -location {510 580} -orientation R0
place_macro -macro_name gen_mem[22].u_mem -location {600 580} -orientation R0
place_macro -macro_name gen_mem[23].u_mem -location {690 580} -orientation R0

place_macro -macro_name gen_mem[24].u_mem -location {60 510} -orientation R0
place_macro -macro_name gen_mem[25].u_mem -location {150 510} -orientation R0
place_macro -macro_name gen_mem[26].u_mem -location {240 510} -orientation R0
place_macro -macro_name gen_mem[27].u_mem -location {330 510} -orientation R0
place_macro -macro_name gen_mem[28].u_mem -location {420 510} -orientation R0
place_macro -macro_name gen_mem[29].u_mem -location {510 510} -orientation R0
place_macro -macro_name gen_mem[30].u_mem -location {600 510} -orientation R0
place_macro -macro_name gen_mem[31].u_mem -location {690 510} -orientation R0

place_macro -macro_name gen_mem[32].u_mem -location {60 440} -orientation R0
place_macro -macro_name gen_mem[33].u_mem -location {150 440} -orientation R0
place_macro -macro_name gen_mem[34].u_mem -location {240 440} -orientation R0
place_macro -macro_name gen_mem[35].u_mem -location {330 440} -orientation R0
place_macro -macro_name gen_mem[36].u_mem -location {420 440} -orientation R0
place_macro -macro_name gen_mem[37].u_mem -location {510 440} -orientation R0
place_macro -macro_name gen_mem[38].u_mem -location {600 440} -orientation R0
place_macro -macro_name gen_mem[39].u_mem -location {690 440} -orientation R0

place_macro -macro_name gen_mem[40].u_mem -location {60 370} -orientation R0
place_macro -macro_name gen_mem[41].u_mem -location {150 370} -orientation R0
place_macro -macro_name gen_mem[42].u_mem -location {240 370} -orientation R0
place_macro -macro_name gen_mem[43].u_mem -location {330 370} -orientation R0
place_macro -macro_name gen_mem[44].u_mem -location {420 370} -orientation R0
place_macro -macro_name gen_mem[45].u_mem -location {510 370} -orientation R0
place_macro -macro_name gen_mem[46].u_mem -location {600 370} -orientation R0
place_macro -macro_name gen_mem[47].u_mem -location {690 370} -orientation R0

place_macro -macro_name gen_mem[48].u_mem -location {240 300} -orientation R0
place_macro -macro_name gen_mem[49].u_mem -location {420 300} -orientation R0
EOF
'

echo "Installed practical_macro_soc_50 into ORFS:"
echo "  ${FLOW_DIR}/designs/src/${DESIGN_NAME}/${DESIGN_NAME}.v"
echo "  ${FLOW_DIR}/designs/nangate45/${DESIGN_NAME}/config.mk"
echo "  ${FLOW_DIR}/designs/nangate45/${DESIGN_NAME}/constraint.sdc"
echo "  ${FLOW_DIR}/designs/nangate45/${DESIGN_NAME}/io.tcl"
echo "  ${FLOW_DIR}/designs/nangate45/${DESIGN_NAME}/macro_placement.tcl"
