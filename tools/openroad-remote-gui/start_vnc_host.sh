#!/usr/bin/env bash
set -euo pipefail

DISPLAY_NUM="${DISPLAY_NUM:-1}"
GEOMETRY="${GEOMETRY:-1600x900}"
DEPTH="${DEPTH:-24}"

if [[ ! -f /root/.vnc/passwd ]]; then
  echo "Missing /root/.vnc/passwd. Run: vncpasswd"
  exit 1
fi

vncserver -kill ":${DISPLAY_NUM}" >/dev/null 2>&1 || true
rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}"

vncserver ":${DISPLAY_NUM}" -localhost yes -geometry "${GEOMETRY}" -depth "${DEPTH}"

echo "VNC server started on localhost:59${DISPLAY_NUM}"
echo "Tunnel from your local machine with:"
echo "  ssh -L 590${DISPLAY_NUM}:127.0.0.1:590${DISPLAY_NUM} Ubuntu"
echo "Then connect your VNC viewer to: 127.0.0.1:590${DISPLAY_NUM}"
echo "Inside the VNC desktop, run: openroad -gui"
