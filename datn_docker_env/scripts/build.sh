#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/build.log"
mkdir -p "${LOG_DIR}"
BASE_IMAGE="${BASE_IMAGE:-ubuntu:22.04}"

{
  echo "Bắt đầu build Docker image..."
  echo "Thư mục project: ${ROOT_DIR}"
  echo "Base image: ${BASE_IMAGE}"
  cd "${ROOT_DIR}"
  DOCKER_BUILDKIT=0 docker build --build-arg BASE_IMAGE="${BASE_IMAGE}" -t datn-openroad-rl:latest .
  echo "Build hoàn tất."
} 2>&1 | tee "${LOG_FILE}"
