#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DREAMPLACE_DIR="${DREAMPLACE_DIR:-${ROOT_DIR}/DREAMPlace}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
JOBS="${JOBS:-$(nproc)}"

if [[ ! -d "${DREAMPLACE_DIR}/.git" ]]; then
  git clone --recursive https://github.com/limbo018/DREAMPlace.git "${DREAMPLACE_DIR}"
else
  git -C "${DREAMPLACE_DIR}" submodule update --init --recursive
fi

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

if command -v nvcc >/dev/null 2>&1; then
  export CMAKE_ARGS="${CMAKE_ARGS:-} -DCMAKE_CUDA_COMPILER=$(command -v nvcc)"
  echo "CUDA detected: $(nvcc --version | tail -1)"
else
  echo "CUDA compiler not found; building DREAMPlace in CPU mode."
fi

cmake -S "${DREAMPLACE_DIR}" -B "${DREAMPLACE_DIR}/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "${DREAMPLACE_DIR}/build" -j "${JOBS}"

if [[ -f "${DREAMPLACE_DIR}/test/ispd2005/adaptec1.json" ]]; then
  (cd "${DREAMPLACE_DIR}" && "${PYTHON_BIN}" dreamplace/Placer.py test/ispd2005/adaptec1.json)
else
  echo "DREAMPlace built, but example JSON was not found; skipping example run."
fi
