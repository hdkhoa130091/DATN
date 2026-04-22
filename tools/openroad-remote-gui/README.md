# OpenROAD Remote GUI

This helper sets up a lightweight remote desktop on the host so `openroad -gui`
does not rely on slow SSH X11 forwarding.

## Why this helps

`openroad -gui` over `ssh -X/-Y` can freeze even when CPU and RAM are fine.
The bottleneck is often remote X11 rendering latency, especially with Docker or
double-SSH forwarding.

Using TigerVNC keeps the GUI on the remote host and streams the desktop instead.

## One-time install on the host

```bash
cd /home/DATN/tools/openroad-remote-gui
chmod +x *.sh
./install_vnc_host.sh
vncpasswd
```

## Start the remote desktop

```bash
cd /home/DATN/tools/openroad-remote-gui
./start_vnc_host.sh
```

Defaults:

- display: `:1`
- local-only VNC port on the host: `5901`
- geometry: `1600x900`

Optional:

```bash
DISPLAY_NUM=2 GEOMETRY=1920x1080 ./start_vnc_host.sh
```

## Connect from your local machine

Create an SSH tunnel:

```bash
ssh -L 5901:127.0.0.1:5901 Ubuntu
```

Run that command on your local machine, not inside the remote server shell.

Then open your VNC client to:

```text
127.0.0.1:5901
```

## Run OpenROAD inside the remote desktop

Open the terminal in the VNC desktop and run:

```bash
openroad -gui
```

Suggested first test:

```tcl
read_db /home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/2_floorplan.odb
gui::fit
```

## Stop the remote desktop

```bash
cd /home/DATN/tools/openroad-remote-gui
./stop_vnc_host.sh
```
