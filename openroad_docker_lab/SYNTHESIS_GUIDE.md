# Yosys and OpenROAD Synthesis Workflow

This guide describes the reusable scripts provided by this repository for
running RTL synthesis, floorplanning, and placement with the Nangate45
technology.

## Workflow Scripts

### `run_cli.sh`

Opens an interactive shell in the persistent `openroad_cli` container:

```bash
./openroad_docker_lab/scripts/run_cli.sh
```

The repository is mounted at `/workspace/DATN` inside the container. An existing
container is restarted and reused instead of being recreated.

### `run_orfs_design.sh`

Runs a design described by an OpenROAD-flow-scripts configuration file:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  <design-config.mk> [synth|floorplan|place]
```

Arguments:

- `<design-config.mk>` is relative to
  `openroad_docker_lab/OpenROAD-flow-scripts/flow/`.
- `synth` runs Yosys synthesis and creates an OpenROAD database.
- `floorplan` runs synthesis followed by OpenROAD floorplanning.
- `place` runs synthesis, floorplanning, and placement.
- The stage defaults to `synth` when the second argument is omitted.

Optional environment variables:

```text
JOBS             Number of parallel make jobs. Default: 1
FLOW_VARIANT     Name of the output run. Default: datn
CONTAINER_NAME   Docker container name. Default: openroad_cli
IMAGE_NAME       Docker image name. Default: openroad-docker-lab:latest
```

Example:

```bash
JOBS=4 FLOW_VARIANT=experiment_01 \
  ./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk place
```

### `run_ariane133_orfs.sh`

Runs the predefined Ariane133 Nangate45 flow:

```bash
JOBS=1 FLOW_VARIANT=datn \
  ./openroad_docker_lab/scripts/run_ariane133_orfs.sh
```

The script performs synthesis, floorplanning, placement, and DEF export.

## Adding a New Design

An ORFS testcase uses the following structure:

```text
flow/designs/src/<design>/<top>.v
flow/designs/nangate45/<design>/config.mk
flow/designs/nangate45/<design>/constraint.sdc
```

The version-controlled template is located at:

```text
openroad_docker_lab/examples/custom_design/
```

Create an `adder_demo` testcase:

```bash
FLOW=openroad_docker_lab/OpenROAD-flow-scripts/flow

mkdir -p "$FLOW/designs/src/adder_demo"
mkdir -p "$FLOW/designs/nangate45/adder_demo"

cp openroad_docker_lab/examples/custom_design/my_top.v \
  "$FLOW/designs/src/adder_demo/adder_demo.v"
cp openroad_docker_lab/examples/custom_design/config.mk \
  "$FLOW/designs/nangate45/adder_demo/config.mk"
cp openroad_docker_lab/examples/custom_design/constraint.sdc \
  "$FLOW/designs/nangate45/adder_demo/constraint.sdc"
```

Update the copied files:

1. Rename the top-level Verilog module to `adder_demo`.
2. Set `DESIGN_NAME` and `DESIGN_NICKNAME` to `adder_demo`.
3. Set `VERILOG_FILES` to the copied RTL file.
4. Set the clock port and period in `constraint.sdc`.

## Design Configuration

A minimal Nangate45 `config.mk` is:

```make
export DESIGN_NAME = adder_demo
export DESIGN_NICKNAME = adder_demo
export PLATFORM = nangate45

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/adder_demo.v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

export CORE_UTILIZATION = 50
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export ABC_AREA = 1
```

`DESIGN_NAME` must exactly match the top-level module name.

For a design with multiple RTL files:

```make
export VERILOG_FILES = \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/top.v \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/alu.v \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/control.v
```

For a design containing hard macros such as SRAM blocks:

```make
export ADDITIONAL_LEFS = /path/to/memory.lef
export ADDITIONAL_LIBS = /path/to/memory.lib
```

LEF describes the physical macro geometry and pins. Liberty describes timing,
power, area, and logical behavior.

## Timing Constraints

For a sequential design with a `clk` input and a 10 ns clock period:

```tcl
create_clock -name core_clock -period 10.0 [get_ports clk]
```

A 10 ns period represents a 100 MHz clock. The port name in `get_ports` must
match the RTL top-level clock port.

An empty SDC file can be used for a purely combinational smoke test. Real timing
analysis should also define appropriate input delays, output delays, and clock
uncertainty.

## Running Synthesis

Command:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk synth
```

The script executes:

```text
RTL parsing and hierarchy elaboration
-> Yosys logic synthesis and optimization
-> ABC technology mapping with Nangate45 Liberty cells
-> Gate-level Verilog generation
-> OpenROAD database generation
```

The underlying ORFS target is:

```bash
make DESIGN_CONFIG=designs/nangate45/adder_demo/config.mk \
  FLOW_VARIANT=datn synth
```

Output directory:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  results/nangate45/adder_demo/datn/
```

Primary synthesis outputs:

```text
1_2_yosys.v    Technology-mapped gate-level Verilog netlist
1_synth.odb    OpenROAD database containing the synthesized design
1_synth.sdc    Timing constraints used by downstream stages
```

Synthesis logs:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  logs/nangate45/adder_demo/datn/
```

The most relevant Yosys log is `1_2_yosys.log`.

## Running Floorplanning

Command:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk floorplan
```

The script runs:

```text
make ... synth
make ... do-floorplan
```

Main output:

```text
results/nangate45/adder_demo/datn/2_floorplan.odb
```

This database includes the die/core area, rows, tracks, I/O placement, macro
placement when applicable, tap cells, and power distribution setup.

## Running Placement

Command:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk place
```

The script runs:

```text
make ... synth
make ... do-floorplan
make ... do-place
```

Main output:

```text
results/nangate45/adder_demo/datn/3_place.odb
```

The placement stage performs global placement, I/O placement, timing-driven
resizing, and detailed placement according to the ORFS flow configuration.

## Ariane133 Outputs

Command:

```bash
JOBS=1 ./openroad_docker_lab/scripts/run_ariane133_orfs.sh
```

Output directory:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  results/nangate45/ariane133/datn/
```

Primary outputs:

```text
1_synth.odb       Synthesized OpenROAD database
2_floorplan.odb   Floorplanned database
3_place.odb       Placed database
3_place.def       DEF exported from the placed database
```

## Relationship to the RL Input

The OpenROAD flow produces ODB and DEF files. The current PPO environment reads:

```text
netlist.pb.txt
initial.plc
```

The legacy TILOS conversion flow used the OpenROAD `partition_design` command to
generate a hypergraph before producing these files. That command is not
available in the current OpenROAD build. Ariane133 training therefore uses the
existing benchmark files:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
```

Run PPO on the GPU host:

```bash
source rl_env/bin/activate

EPISODES=10 ROLLOUT_EPISODES=2 BATCH_SIZE=1 MAX_EDGES=4000 \
  ./rl_macroplacement_agent/scripts/run_ariane133_ppo.sh
```
