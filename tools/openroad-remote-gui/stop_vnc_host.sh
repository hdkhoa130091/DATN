#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${DISPLAY_NUM:-1}"
vncserver -kill ":${DISPLAY_NUM}"
