#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FLOW_DIR="${ROOT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow"
SRC_DIR="${FLOW_DIR}/designs/src/macro_cluster_demo"
CFG_DIR="${FLOW_DIR}/designs/nangate45/macro_cluster_demo"

mkdir -p "${SRC_DIR}" "${CFG_DIR}"

cp "${ROOT_DIR}/example/macro_cluster_demo.v" "${SRC_DIR}/macro_cluster_demo.v"

cat > "${CFG_DIR}/config.mk" <<'EOF'
export DESIGN_NAME = macro_cluster_demo
export DESIGN_NICKNAME = macro_cluster_demo
export PLATFORM = nangate45

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/macro_cluster_demo.v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

export ADDITIONAL_LEFS = $(PLATFORM_DIR)/lef/fakeram45_256x16.lef
export ADDITIONAL_LIBS = $(PLATFORM_DIR)/lib/fakeram45_256x16.lib
export PRESERVE_CELLS = fakeram45_256x16

export DIE_AREA = 0 0 500 500
export CORE_AREA = 20 20 480 480

export PLACE_DENSITY = 0.45
export ABC_AREA = 1
EOF

cat > "${CFG_DIR}/constraint.sdc" <<'EOF'
create_clock -name core_clock -period 10.0 [get_ports clk]
set_input_delay 0.2 -clock core_clock [get_ports rst_n]
set_input_delay 0.2 -clock core_clock [get_ports start]
set_output_delay 0.2 -clock core_clock [get_ports gpio_out*]
EOF

echo "Installed macro_cluster_demo into ORFS:"
echo "  ${SRC_DIR}/macro_cluster_demo.v"
echo "  ${CFG_DIR}/config.mk"
echo "  ${CFG_DIR}/constraint.sdc"
