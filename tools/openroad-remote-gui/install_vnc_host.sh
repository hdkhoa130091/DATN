#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  tigervnc-standalone-server \
  tigervnc-common \
  openbox \
  python3-xdg \
  xterm \
  dbus-x11 \
  x11-xserver-utils

mkdir -p /root/.vnc

cat >/root/.vnc/xstartup <<'EOF'
#!/usr/bin/env bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
export XDG_SESSION_TYPE=x11
export XDG_CURRENT_DESKTOP=Openbox
export XDG_RUNTIME_DIR=/tmp/xdg-runtime-root
export LANG=C.UTF-8
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
xsetroot -solid "#20242b"
openbox &
xterm -fa Monospace -fs 11 -geometry 120x30+40+40
EOF

chmod +x /root/.vnc/xstartup

echo "Installed VNC host packages."
echo "Next:"
echo "  1. Set VNC password: vncpasswd"
echo "  2. Start server: /home/DATN/tools/openroad-remote-gui/start_vnc_host.sh"
