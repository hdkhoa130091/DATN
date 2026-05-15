#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DREAMPLACE_DIR="${DREAMPLACE_DIR:-${ROOT_DIR}/DREAMPlace}"
INSTALL_DIR="${INSTALL_DIR:-${DREAMPLACE_DIR}/install}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
JOBS="${JOBS:-$(nproc)}"
RUN_SMOKE_TEST="${RUN_SMOKE_TEST:-0}"
CUDA_NVCC_BIN="${CUDA_NVCC_BIN:-}"

if [[ ! -d "${DREAMPLACE_DIR}/.git" ]]; then
  git clone --recursive https://github.com/limbo018/DREAMPlace.git "${DREAMPLACE_DIR}"
else
  git -C "${DREAMPLACE_DIR}" submodule update --init --recursive
fi

patch_cuda12_cub_namespace() {
  local target="${DREAMPLACE_DIR}/dreamplace/ops/utility/src/utils_cub.cuh"
  "${PYTHON_BIN}" - "${target}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old = """// include cub in a safe manner
#define CUB_NS_PREFIX namespace DREAMPLACE_NAMESPACE {
#define CUB_NS_POSTFIX }
#define CUB_NS_QUALIFIER DREAMPLACE_NAMESPACE::cub
#include "cub/cub.cuh"
#undef CUB_NS_QUALIFIER
#undef CUB_NS_POSTFIX
#undef CUB_NS_PREFIX
"""
new = """// CUDA 12.x CUB uses ::cuda::std internally. If CUB is wrapped inside the
// DREAMPlace namespace, those references can resolve to DREAMPLACE_NAMESPACE::cuda
// from limits.h instead of NVIDIA's global ::cuda namespace. Keep the legacy
// wrapped namespace for older toolkits, but use the global CUB namespace on CUDA
// 12+ and alias it back into DREAMPlace for existing call sites.
#if defined(__CUDACC_VER_MAJOR__) && (__CUDACC_VER_MAJOR__ >= 12)
#include "cub/cub.cuh"
namespace DREAMPLACE_NAMESPACE { namespace cub = ::cub; }
#else
#define CUB_NS_PREFIX namespace DREAMPLACE_NAMESPACE {
#define CUB_NS_POSTFIX }
#define CUB_NS_QUALIFIER DREAMPLACE_NAMESPACE::cub
#include "cub/cub.cuh"
#undef CUB_NS_QUALIFIER
#undef CUB_NS_POSTFIX
#undef CUB_NS_PREFIX
#endif
"""
if new in text:
    print("CUDA 12 CUB namespace patch already present.")
elif old in text:
    path.write_text(text.replace(old, new))
    print("Applied CUDA 12 CUB namespace patch.")
else:
    raise SystemExit(f"Could not find expected CUB include block in {path}")
PY
}

if ! "${PYTHON_BIN}" -m pip --version >/dev/null 2>&1; then
  echo "Missing pip for ${PYTHON_BIN}. Install it first, for example:"
  echo "  sudo apt-get update && sudo apt-get install -y python3-pip"
  exit 2
fi

if ! command -v cmake >/dev/null 2>&1; then
  echo "Missing cmake. Install it first, for example:"
  echo "  sudo apt-get update && sudo apt-get install -y cmake build-essential"
  exit 2
fi

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/rl_macroplacement_agent/requirements.txt"
"${PYTHON_BIN}" -m pip install \
  shapely \
  cairocffi \
  torch-optimizer \
  ncg-optimizer \
  scipy \
  matplotlib \
  pyunpack \
  patool

HAS_CUDA=0
if [[ -z "${CUDA_NVCC_BIN}" ]]; then
  if command -v nvcc >/dev/null 2>&1; then
    CUDA_NVCC_BIN="$(command -v nvcc)"
  elif [[ -x /usr/local/cuda/bin/nvcc ]]; then
    CUDA_NVCC_BIN="/usr/local/cuda/bin/nvcc"
  fi
fi

if [[ -n "${CUDA_NVCC_BIN}" ]]; then
  HAS_CUDA=1
  export PATH="$(dirname "${CUDA_NVCC_BIN}"):${PATH}"
  echo "CUDA detected: $("${CUDA_NVCC_BIN}" --version | tail -1)"
  patch_cuda12_cub_namespace
else
  echo "CUDA compiler not found; building DREAMPlace in CPU mode."
fi

cmake_args=(
  -S "${DREAMPLACE_DIR}"
  -B "${DREAMPLACE_DIR}/build"
  -DCMAKE_BUILD_TYPE=Release
  -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}"
  -DPython_EXECUTABLE="${PYTHON_BIN}"
)
if [[ -n "${CUDA_NVCC_BIN}" ]]; then
  cmake_args+=("-DCMAKE_CUDA_COMPILER=${CUDA_NVCC_BIN}")
fi

cmake "${cmake_args[@]}"
cmake --build "${DREAMPLACE_DIR}/build" -j "${JOBS}"
cmake --install "${DREAMPLACE_DIR}/build" --prefix "${INSTALL_DIR}"

echo "DREAMPlace installed at: ${INSTALL_DIR}"
echo "Run it from the installed tree so generated modules such as dreamplace.configure are available."

if [[ "${RUN_SMOKE_TEST}" == "1" ]]; then
  JSON_PATH="${INSTALL_DIR}/test/ispd2005/adaptec1.json"
  if [[ -f "${JSON_PATH}" ]]; then
    if [[ ! -f "${INSTALL_DIR}/benchmarks/ispd2005/adaptec1/adaptec1.aux" ]]; then
      echo "Downloading ISPD2005 benchmarks for smoke test."
      (
        cd "${INSTALL_DIR}/benchmarks"
        PATH="$(dirname "${PYTHON_BIN}"):${PATH}" \
          "${PYTHON_BIN}" ispd2005_2015.py
      )
    fi
    SMOKE_JSON="${JSON_PATH}"
    if [[ "${HAS_CUDA}" == "0" ]]; then
      SMOKE_JSON="${INSTALL_DIR}/test/ispd2005/adaptec1_cpu.json"
      cp "${JSON_PATH}" "${SMOKE_JSON}"
      sed -i 's/"gpu"[[:space:]]*:[[:space:]]*1/"gpu" : 0/' "${SMOKE_JSON}"
    fi
    echo "Running optional DREAMPlace smoke test with ${SMOKE_JSON}"
    (
      cd "${INSTALL_DIR}"
      PYTHONPATH="${INSTALL_DIR}:${PYTHONPATH:-}" \
        "${PYTHON_BIN}" dreamplace/Placer.py "${SMOKE_JSON}"
    )
  else
    echo "DREAMPlace installed, but example JSON was not found at ${JSON_PATH}; skipping smoke test."
  fi
fi
