#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FLOW_ROOT="${ROOT_DIR}/openroad_docker_lab/OpenROAD-flow-scripts/flow"

PLATFORM="${1:-}"
DESIGN="${2:-}"
FLOW_VARIANT="${3:-}"
RUN_NAME="${4:-${FLOW_VARIANT}}"

usage() {
  cat <<EOF
Usage:
  $0 <platform> <design> <flow_variant> [run_name]

Example:
  $0 nangate45 ariane133 place_run_01 ariane133_orfs
  $0 nangate45 simple_sram sram_run_01 simple_sram_orfs
EOF
}

if [[ -z "${PLATFORM}" || -z "${DESIGN}" || -z "${FLOW_VARIANT}" ]]; then
  usage
  exit 2
fi

CONFIG_MK="${FLOW_ROOT}/designs/${PLATFORM}/${DESIGN}/config.mk"
RESULT_DIR="${FLOW_ROOT}/results/${PLATFORM}/${DESIGN}/${FLOW_VARIANT}"

if [[ ! -f "${CONFIG_MK}" ]]; then
  echo "Missing config: ${CONFIG_MK}"
  exit 1
fi

if [[ ! -d "${RESULT_DIR}" ]]; then
  echo "Missing ORFS result directory: ${RESULT_DIR}"
  exit 1
fi

if [[ ! -f "${RESULT_DIR}/3_place.def" ]]; then
  if [[ -f "${RESULT_DIR}/3_place.odb" ]]; then
    echo "Placement DEF missing; exporting ${RESULT_DIR}/3_place.def from 3_place.odb"
    (
      cd "${FLOW_ROOT}"
      ODB_FILE="${RESULT_DIR}/3_place.odb" \
      DEF_FILE="${RESULT_DIR}/3_place.def" \
      openroad "${FLOW_ROOT}/scripts/write_def.tcl"
    )
  else
    echo "Missing placement outputs:"
    echo "  ${RESULT_DIR}/3_place.def"
    echo "  ${RESULT_DIR}/3_place.odb"
    echo "Run ORFS to stage 'place' first."
    exit 1
  fi
fi

if [[ ! -f "${RESULT_DIR}/1_2_yosys.v" ]]; then
  echo "Missing synthesized netlist: ${RESULT_DIR}/1_2_yosys.v"
  exit 1
fi

DESIGN_NAME="$(sed -n 's/^export DESIGN_NAME *= *//p' "${CONFIG_MK}" | head -n 1 | xargs)"
if [[ -z "${DESIGN_NAME}" ]]; then
  echo "Could not parse DESIGN_NAME from ${CONFIG_MK}"
  exit 1
fi

map_platform_dir() {
  case "$1" in
    nangate45) echo "NanGate45" ;;
    asap7) echo "ASAP7" ;;
    sky130hd) echo "SKY130HD" ;;
    *) echo "" ;;
  esac
}

map_site() {
  case "$1" in
    nangate45) echo "FreePDK45_38x28_10R_NP_162NW_34O" ;;
    asap7) echo "asap7sc7p5t" ;;
    sky130hd) echo "unithd" ;;
    *) echo "" ;;
  esac
}

map_halo() {
  case "$1" in
    nangate45) echo "5" ;;
    asap7) echo "1" ;;
    sky130hd) echo "5" ;;
    *) echo "" ;;
  esac
}

PLATFORM_DIR_NAME="$(map_platform_dir "${PLATFORM}")"
SITE_NAME="$(map_site "${PLATFORM}")"
HALO_WIDTH="$(map_halo "${PLATFORM}")"

if [[ -z "${PLATFORM_DIR_NAME}" || -z "${SITE_NAME}" || -z "${HALO_WIDTH}" ]]; then
  echo "Unsupported platform: ${PLATFORM}"
  exit 1
fi

RUN_DIR="${ROOT_DIR}/MacroPlacement/Flows/${PLATFORM_DIR_NAME}/generated/${DESIGN}/${RUN_NAME}"
DEF_DIR="${RUN_DIR}/def"
LIB_DIR="${RUN_DIR}/lib"
LEF_DIR="${RUN_DIR}/lef"
LOG_DIR="${RUN_DIR}/log"

rm -rf "${RUN_DIR}"
mkdir -p "${DEF_DIR}" "${LIB_DIR}" "${LEF_DIR}" "${LOG_DIR}"

cp "${RESULT_DIR}/3_place.def" "${DEF_DIR}/${DESIGN_NAME}.def"
cp "${RESULT_DIR}/1_2_yosys.v" "${DEF_DIR}/${DESIGN_NAME}.v"

copy_if_exists() {
  local src="$1"
  local dst_dir="$2"
  if [[ -f "${src}" ]]; then
    cp "${src}" "${dst_dir}/"
  fi
}

case "${PLATFORM}" in
  nangate45)
    copy_if_exists "${ROOT_DIR}/MacroPlacement/Enablements/NanGate45/lib/NangateOpenCellLibrary_typical.lib" "${LIB_DIR}"
    copy_if_exists "${ROOT_DIR}/MacroPlacement/Enablements/NanGate45/lef/NangateOpenCellLibrary.tech.lef" "${LEF_DIR}"
    copy_if_exists "${ROOT_DIR}/MacroPlacement/Enablements/NanGate45/lef/NangateOpenCellLibrary.macro.mod.lef" "${LEF_DIR}"
    ;;
  asap7)
    find "${ROOT_DIR}/MacroPlacement/Enablements/ASAP7/lib" -maxdepth 1 -name '*.lib' -exec cp {} "${LIB_DIR}/" \;
    find "${ROOT_DIR}/MacroPlacement/Enablements/ASAP7/lef" -maxdepth 1 -name '*.lef' -exec cp {} "${LEF_DIR}/" \;
    ;;
  sky130hd)
    find "${ROOT_DIR}/MacroPlacement/Enablements/SKY130HD/lib" -maxdepth 1 -name '*.lib' -exec cp {} "${LIB_DIR}/" \;
    find "${ROOT_DIR}/MacroPlacement/Enablements/SKY130HD/lef" -maxdepth 1 \( -name '*.lef' -o -name '*.tlef' \) -exec cp {} "${LEF_DIR}/" \;
    ;;
esac

extract_paths() {
  local key="$1"
  sed -n "s/^export ${key} *= *//p" "${CONFIG_MK}" | sed 's/\\$//' | tr -d '\r'
}

copy_config_file_list() {
  local value="$1"
  local dst_dir="$2"
  [[ -z "${value}" ]] && return 0
  while read -r token; do
    [[ -z "${token}" ]] && continue
    token="${token//'$(PLATFORM_DIR)'/platforms/${PLATFORM}}"
    token="${token//'$(DESIGN_HOME)'/designs}"
    case "${token}" in
      ./designs/*)
        local src="${FLOW_ROOT}/${token#./}"
        copy_if_exists "${src}" "${dst_dir}"
        ;;
      \$*|*'$('*|*')'*)
        ;;
      *)
        if [[ -f "${FLOW_ROOT}/${token}" ]]; then
          copy_if_exists "${FLOW_ROOT}/${token}" "${dst_dir}"
        fi
        ;;
    esac
  done < <(printf '%s\n' "${value}" | xargs -n 1 echo)
}

copy_config_file_list "$(extract_paths ADDITIONAL_LIBS)" "${LIB_DIR}"
copy_config_file_list "$(extract_paths ADDITIONAL_LEFS)" "${LEF_DIR}"

cat > "${RUN_DIR}/design_setup.tcl" <<EOF
set DESIGN ${DESIGN_NAME}
set SITE "${SITE_NAME}"
set HALO_WIDTH ${HALO_WIDTH}
EOF

cat > "${RUN_DIR}/openroad" <<EOF
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_PATH="\${1:-}"
if [ -z "\$SCRIPT_PATH" ]; then
  echo "usage: ./openroad <script.tcl>" >&2
  exit 2
fi
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="\$(cd "\${SCRIPT_DIR}/../../../../../.." && pwd)"
python3 "\${REPO_ROOT}/MacroPlacement/Flows/util/openroad_partition_compat.py" "\$SCRIPT_PATH"
EOF
chmod +x "${RUN_DIR}/openroad"

{
  echo "set libdir \"./lib\""
  echo "set lefdir \"./lef\""
  echo "set qrcdir \"./qrc\""
  echo
  echo "set libworst \""
  find "${LIB_DIR}" -maxdepth 1 -type f -name '*.lib' -printf '    ${libdir}/%f\n' | sort
  echo "\""
  echo
  echo "set libbest \""
  find "${LIB_DIR}" -maxdepth 1 -type f -name '*.lib' -printf '    ${libdir}/%f\n' | sort
  echo "\""
  echo
  echo "set lefs \""
  find "${LEF_DIR}" -maxdepth 1 -type f \( -name '*.tlef' -o -name '*.tech.lef' \) -printf '    ${lefdir}/%f\n' | sort
  find "${LEF_DIR}" -maxdepth 1 -type f \( -name '*.lef' -o -name '*.tlef' \) ! -name '*.tech.lef' ! -name '*.tlef' -printf '    ${lefdir}/%f\n' | sort
  echo "\""
} > "${RUN_DIR}/lib_setup.tcl"

echo "Prepared flow.py run directory:"
echo "  ${RUN_DIR}"
echo
echo "Expected inputs now available:"
echo "  ${RUN_DIR}/design_setup.tcl"
echo "  ${RUN_DIR}/lib_setup.tcl"
echo "  ${RUN_DIR}/openroad"
echo "  ${RUN_DIR}/def/${DESIGN_NAME}.def"
echo "  ${RUN_DIR}/def/${DESIGN_NAME}.v"
echo
echo "Run flow.py with:"
echo "  python ${ROOT_DIR}/MacroPlacement/Flows/util/flow.py \\"
echo "    ${RUN_DIR} ${RUN_DIR}/output_CodeElement"
