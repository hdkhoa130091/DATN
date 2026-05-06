#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
  echo "apt-get not found. Install python3-pip, cmake, build-essential, and git with your system package manager."
  exit 2
fi

APT="${APT:-apt-get}"
SUDO=""
if [[ "${EUID}" -ne 0 ]]; then
  SUDO="${SUDO:-sudo}"
fi

${SUDO} "${APT}" update
${SUDO} "${APT}" install -y \
  build-essential \
  cmake \
  git \
  python3-dev \
  python3-pip \
  python3-venv
