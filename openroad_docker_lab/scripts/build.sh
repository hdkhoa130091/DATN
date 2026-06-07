#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/3] Chuyển tới thư mục project: ${ROOT_DIR}"
cd "${ROOT_DIR}"

echo "[2/3] Bắt đầu build Docker image openroad-docker-lab:latest"
docker build -t openroad-docker-lab:latest .

echo "[3/3] Build hoàn tất."
