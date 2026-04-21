# RL Macro Placement Project - Progress Summary

## Current Milestone

The project has reached a reproducible open-source physical-design milestone:

- ORFS sample design `nangate45/gcd` runs through OpenROAD and produces:
  - `6_final.odb`
  - `6_final.def`
  - `6_final.sdc`
  - `6_final.v`
  - `6_final.spef`
- OpenROAD GUI can be used to inspect light checkpoints such as:
  - `2_floorplan.odb`
  - `3_place.odb`
  - `6_final.odb`
- KLayout-based GDS merge is not required for this milestone and is currently blocked by an older packaged `klayout 0.26.2`.

## Completed Tasks

### 1. Repository Setup
- `MacroPlacement` is present in the repo and remains the main bridge toward open-source macro-placement data generation.
- `circuit_training` is present in the repo for the later RL stage.
- `DREAMPlace` remains optional and is not needed for the current milestone.

### 2. Open-Source Toolchain Validation
- Verified a prebuilt `OpenROAD` binary works on Ubuntu 22.04.
- Verified Ubuntu-packaged `yosys` is too old for current ORFS.
- Verified `oss-cad-suite` provides a newer `yosys` suitable for ORFS.

### 3. ORFS Flow Validation
- Successfully ran `synth`
- Successfully ran `floorplan`
- Successfully ran `place`
- Successfully ran `cts`
- Successfully ran `global_route`
- Successfully ran `detail_route`
- Successfully generated final OpenROAD artifacts before GDS merge

### 4. RL Environment Baseline
- `rl_macro_placement_v2.py` runs as a simplified RL demo
- uses Gymnasium + Stable-Baselines3
- remains separate from the OpenROAD data path for now

## Current Reproducible Command

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad -j1
```

## Compatibility Fix Applied

Current ORFS expects a newer OpenROAD CTS interface than the installed binary supports.

Applied fix:

- remove `-repair_clock_nets` from `clock_tree_synthesis`
- call `repair_clock_nets` as a separate command after CTS

Patched file:

- `/home/DATN/OpenROAD-flow-scripts/flow/scripts/cts.tcl`

## Current Output Artifacts

Important outputs under `/home/DATN/OpenROAD-flow-scripts/flow/results/nangate45/gcd/base`:

- `1_synth.odb`, `1_synth.sdc`
- `2_floorplan.odb`, `2_floorplan.sdc`
- `3_place.odb`, `3_place.sdc`
- `4_cts.odb`, `4_cts.sdc`
- `5_1_grt.odb`, `5_1_grt.sdc`
- `5_route.odb`, `5_route.sdc`
- `6_final.odb`
- `6_final.def`
- `6_final.sdc`
- `6_final.v`
- `6_final.spef`

## Known Issues

### KLayout GDS Merge

- `klayout 0.26.2` currently segfaults during `def2stream.py`
- this blocks `6_1_merged.gds`
- this does not block the current OpenROAD milestone

### GUI Performance

- remote X11 GUI is usable for light checkpoint inspection
- heavy interactive use is still laggy
- preferred workflow is terminal execution plus occasional checkpoint viewing

## Next Steps

1. Reproduce the same `6_final.*` milestone on a stronger machine.
2. Map ORFS intermediate artifacts to the RL data path.
3. Move from sample `gcd` to a `MacroPlacement` testcase.
4. Build the converter path toward `protobuf` and `initial.plc`.
5. Return to GDS/DRC/LVS only after the RL data path is stable.
