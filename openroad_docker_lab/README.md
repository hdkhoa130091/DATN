# OpenROAD Docker Lab

## Introduction

`openroad_docker_lab` is the Docker workspace for the OpenROAD-based digital
implementation flow used in this repository. It packages the toolchain needed
to move from RTL and design configuration files into synthesis, floorplanning,
placement, and the downstream artifacts later consumed by MacroPlacement and
reinforcement learning workflows.

This environment is built around a single Docker image that contains:

- `yosys`
- `yosys-abc`
- `abc`
- `openroad`
- OpenROAD GUI support
- OpenROAD-flow-scripts

The same image is used for both command-line EDA execution and interactive GUI
sessions.

## Image Definition

The lab builds one image:

```text
openroad-docker-lab:latest
```

This image is intended to support the complete OpenROAD-oriented workflow in
the repository, including:

- RTL synthesis
- logic mapping
- floorplan creation
- utilization control
- macro and standard-cell placement
- OpenROAD script execution
- interactive GUI inspection

## Toolchain Contents

The image contains:

- Ubuntu 22.04
- OSS CAD Suite
- Yosys
- Yosys ABC
- ABC
- OpenROAD prebuilt package with GUI support
- OpenROAD-flow-scripts
- Python 3
- Git

## Repository Mount Layout

When a container is started through the provided scripts, the repository is
mounted at:

```text
/workspace/DATN
```

This keeps source files, logs, generated outputs, and exported artifacts in the
host working tree.

## Build

Build the image from the repository root:

```bash
cd /path/to/DATN
./openroad_docker_lab/scripts/build.sh
```

This creates:

```text
openroad-docker-lab:latest
```

The build script also runs an immediate smoke test inside the built image to
verify the expected command-line toolchain is available before the image is
used for EDA flow execution.

## Command-Line EDA Usage

To create or reopen the reusable CLI container:

```bash
cd /path/to/DATN
./openroad_docker_lab/scripts/run_cli.sh
```

This script:

- uses the image `openroad-docker-lab:latest`
- creates the container `openroad_cli` if needed
- starts it if it already exists but is stopped
- opens a shell inside `/workspace/DATN`

Typical commands inside the container:

```bash
yosys -V
openroad -version
cd /workspace/DATN/openroad_docker_lab/OpenROAD-flow-scripts/flow
```

## GUI Usage

To launch the GUI container:

```bash
cd /path/to/DATN
xhost +local:docker
./openroad_docker_lab/scripts/run_gui.sh
```

This script:

- uses the same image `openroad-docker-lab:latest`
- creates a fresh container named `openroad_gui`
- mounts the repository at `/workspace/DATN`
- forwards the X11 display to the container

After entering the container shell, launch the GUI with:

```bash
openroad -gui
```

## Verification

After entering the CLI container, verify the environment with:

```bash
cd /workspace/DATN/openroad_docker_lab
./scripts/test_tools.sh
```

The verification log is written to:

```text
openroad_docker_lab/logs/container_tools.log
```

Representative checks:

```bash
make --version
yosys -V
yosys-abc -h
abc -h
openroad -version
tclsh <<< 'puts [info patchlevel]'
python3 --version
git --version
```

## Docker Compose

The compose file defines two services that use the same image:

- `openroad-cli`
- `openroad-gui`

Example commands:

```bash
cd /path/to/DATN/openroad_docker_lab
docker compose build
docker compose up -d openroad-cli
docker compose run --rm openroad-gui bash
```

## Flow Outputs

The OpenROAD flow produces artifacts such as:

- synthesized Verilog
- SDC constraints
- ODB databases
- DEF files
- floorplan and placement outputs

These outputs are then used by the rest of the repository, including the
MacroPlacement flow and the RL pipeline.

Detailed synthesis, floorplan, placement, and artifact preparation notes are
documented in:

```text
openroad_docker_lab/SYNTHESIS_GUIDE.md
```
