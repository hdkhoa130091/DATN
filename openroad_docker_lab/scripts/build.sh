#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/3] Chuyển tới thư mục project: ${ROOT_DIR}"
cd "${ROOT_DIR}"

echo "[2/3] Building image: openroad-docker-lab:latest"
docker build \
  -t openroad-docker-lab:latest \
  .

echo "[3/3] Running container smoke test"
docker run --rm \
  -v "${ROOT_DIR}:/workspace/DATN/openroad_docker_lab" \
  -w /workspace/DATN/openroad_docker_lab \
  openroad-docker-lab:latest \
  bash -lc './scripts/test_tools.sh'

echo "[4/4] Build và smoke test hoàn tất."
