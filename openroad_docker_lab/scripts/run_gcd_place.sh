#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
ORFS_SRC="/opt/OpenROAD-flow-scripts"
ORFS_DST="${WORKSPACE_ROOT}/OpenROAD-flow-scripts"

if [[ ! -x /usr/local/bin/openroad ]]; then
  echo "openroad not found at /usr/local/bin/openroad"
  exit 1
fi

if [[ ! -x /opt/oss-cad-suite/bin/yosys ]]; then
  echo "yosys not found at /opt/oss-cad-suite/bin/yosys"
  exit 1
fi

if [[ ! -d "${ORFS_DST}" ]]; then
  echo "Copying ORFS into workspace so results persist on host..."
  cp -r "${ORFS_SRC}" "${ORFS_DST}"
fi

export YOSYS_EXE=/opt/oss-cad-suite/bin/yosys
export OPENROAD_EXE=/usr/local/bin/openroad

cd "${ORFS_DST}/flow"
rm -rf results/nangate45/gcd/base logs/nangate45/gcd/base objects/nangate45/gcd/base reports/nangate45/gcd/base
mkdir -p results/nangate45/gcd/base
echo 0.46 > results/nangate45/gcd/base/clock_period.txt

make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE="${YOSYS_EXE}" \
  OPENROAD_EXE="${OPENROAD_EXE}" \
  synth floorplan place -j1

echo
echo "Done. Results on host-mounted workspace:"
echo "  ${ORFS_DST}/flow/results/nangate45/gcd/base"
