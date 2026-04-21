# OpenROAD Current Stage Rebuild

This note captures the exact state reached in `/home/DATN` before moving to a new GPU machine.

## Scope

Current verified milestone:

- `OpenROAD-flow-scripts` sample design `nangate45/gcd` runs through OpenROAD and produces:
  - `6_final.odb`
  - `6_final.def`
  - `6_final.sdc`
  - `6_final.v`
  - `6_final.spef`
- KLayout GDS merge is not required for this milestone and currently fails on the older packaged `klayout 0.26.2`.

This is enough for:

- proving the open-source RTL-to-PnR flow works
- inspecting checkpoints in OpenROAD GUI
- moving on to reading intermediate artifacts for the RL pipeline

## Machine Setup

Use Ubuntu 22.04 or compatible.

Install base packages:

```bash
apt-get update
apt-get install -y \
  curl wget git make cmake ninja-build pkg-config \
  flex bison swig tcl-dev python3 python3-pip python3-venv \
  iverilog verilator klayout magic netgen gtkwave
```

## Repository Setup

```bash
cd /home
git clone <your-repo-url> DATN
cd /home/DATN
```

Clone OpenROAD-flow-scripts separately next to the repo content:

```bash
cd /home/DATN
curl -L https://codeload.github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/tar.gz/refs/heads/master \
  -o orfs.tar.gz
tar -xzf orfs.tar.gz
mv OpenROAD-flow-scripts-master OpenROAD-flow-scripts
rm -f orfs.tar.gz
```

Install OpenROAD binary:

```bash
cd /tmp
curl -L \
  https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb \
  -o openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
apt-get install -y ./openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb
```

Install OSS CAD Suite for a newer `yosys`:

```bash
cd /home/DATN
curl -L \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-04-21/oss-cad-suite-linux-x64-20260421.tgz \
  -o oss-cad-suite-linux-x64-20260421.tgz
mkdir -p /home/DATN/oss-cad-suite-20260421
tar -xzf oss-cad-suite-linux-x64-20260421.tgz -C /home/DATN/oss-cad-suite-20260421 --strip-components=1
```

## Required Compatibility Patch

The current ORFS revision expects a newer OpenROAD interface for CTS.
Patch `flow/scripts/cts.tcl` after unpacking ORFS:

```diff
--- a/flow/scripts/cts.tcl
+++ b/flow/scripts/cts.tcl
@@
-set cts_args [list \
-  -sink_clustering_enable \
-  -repair_clock_nets]
+set cts_args [list \
+  -sink_clustering_enable]
@@
 log_cmd clock_tree_synthesis {*}$cts_args
+log_cmd repair_clock_nets
```

Quick shell patch:

```bash
python3 - <<'PY'
from pathlib import Path
path = Path('/home/DATN/OpenROAD-flow-scripts/flow/scripts/cts.tcl')
text = path.read_text()
text = text.replace(
    "set cts_args [list \\\n  -sink_clustering_enable \\\n  -repair_clock_nets]",
    "set cts_args [list \\\n  -sink_clustering_enable]"
)
text = text.replace(
    "log_cmd clock_tree_synthesis {*}$cts_args\n",
    "log_cmd clock_tree_synthesis {*}$cts_args\nlog_cmd repair_clock_nets\n",
    1,
)
path.write_text(text)
PY
```

## Run To The Current Milestone

Run the flow in terminal mode:

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad -j1
```

Important notes:

- `-j1` avoids race/issues on this setup.
- `env -u DISPLAY QT_QPA_PLATFORM=offscreen` prevents Qt/X11 issues in terminal-only runs.
- The flow may stop at the KLayout GDS merge step because packaged `klayout 0.26.2` segfaults.

## Current Successful Output

After the run, these files should exist:

```text
/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/6_final.odb
/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/6_final.def
/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/6_final.sdc
/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/6_final.v
/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/6_final.spef
```

## Optional GUI Checkpoint Viewing

Use a separate SSH/X11 session only when you want to inspect checkpoints:

```bash
openroad -gui
```

Then in the OpenROAD Tcl input:

```tcl
read_db /home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/2_floorplan.odb
gui::fit
```

Later:

```tcl
read_db /home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/3_place.odb
gui::fit
```

And finally:

```tcl
read_db /home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base/6_final.odb
gui::fit
```

## What Not To Chase Yet

- Do not block on KLayout GDS merge for now.
- Do not spend time on GUI performance tuning beyond basic checkpoint inspection.
- Do not start RL training on OpenROAD outputs until the intermediate file mapping is documented.

## Next Step After Rebuild

Once `6_final.*` is reproduced again, continue with:

1. mapping `synth/floorplan/place/cts/route/final` artifacts to the RL pipeline
2. identifying which DEF/LEF/netlist data must be converted into `protobuf` and `initial.plc`
3. moving from ORFS sample `gcd` to a `MacroPlacement` testcase
