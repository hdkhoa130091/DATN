# Huong dan synthesis thiet ke bat ky voi Yosys va OpenROAD

Tai lieu nay huong dan tao mot testcase RTL moi, synthesis bang Yosys, sau do
tuy chon chay floorplan va placement bang OpenROAD-flow-scripts (ORFS).

## 1. Dieu kien ban dau

Thuc hien tren may local co Docker:

```bash
cd /home/khoahd/Documents/DATN-1
docker image inspect openroad-docker-lab:latest
```

Neu image chua ton tai:

```bash
./openroad_docker_lab/scripts/build.sh
```

Mo terminal trong container khi can kiem tra thu cong:

```bash
./openroad_docker_lab/scripts/run_cli.sh
```

Repository tren host duoc mount vao `/workspace/DATN` trong container.
Container `openroad_cli` duoc tai su dung, khong bi xoa moi lan chay.

## 2. Cau truc mot testcase

ORFS can ba thanh phan chinh:

```text
designs/src/<ten_testcase>/<top>.v
designs/nangate45/<ten_testcase>/config.mk
designs/nangate45/<ten_testcase>/constraint.sdc
```

Template cua repository nam tai:

```text
openroad_docker_lab/examples/custom_design/
```

Tao testcase moi, vi du `adder_demo`:

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

Sau do sua:

- `adder_demo.v`: doi ten module top thanh `adder_demo`.
- `config.mk`: doi `DESIGN_NAME`, `DESIGN_NICKNAME` va ten file Verilog.
- `constraint.sdc`: doi port clock va chu ky clock.

## 3. Noi dung config.mk

Mau toi thieu:

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

`DESIGN_NAME` phai trung voi ten module top trong Verilog.

Neu design co nhieu file RTL:

```make
export VERILOG_FILES = \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/top.v \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/alu.v \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/control.v
```

Neu design co macro SRAM, can khai bao them LEF va Liberty:

```make
export ADDITIONAL_LEFS = /duong/dan/toi/memory.lef
export ADDITIONAL_LIBS = /duong/dan/toi/memory.lib
```

## 4. Noi dung constraint.sdc

Voi mach co clock:

```tcl
create_clock -name core_clock -period 10.0 [get_ports clk]
```

`period 10.0` tuong ung clock 100 MHz. Port `clk` phai ton tai trong module top.

Voi mach to hop khong co clock, co the de file SDC rong. Tuy nhien nen bo sung
input/output delay khi can phan tich timing nghiem tuc.

## 5. Chay synthesis

Tu thu muc goc repository:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk synth
```

Buoc nay thuc hien:

```text
RTL Verilog
-> Yosys elaboration va optimization
-> ABC technology mapping
-> Nangate45 standard cells
-> OpenROAD database
```

Ket qua:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/results/nangate45/adder_demo/datn/
```

File quan trong:

- `1_2_yosys.v`: gate-level netlist sau technology mapping.
- `1_synth.odb`: database synthesis cho OpenROAD.
- `1_synth.sdc`: timing constraints cua design.

Log Yosys:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/logs/nangate45/adder_demo/datn/
```

## 6. Chay floorplan hoac placement

Synthesis va floorplan:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk floorplan
```

Synthesis, floorplan va placement:

```bash
./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk place
```

Co the tang so job:

```bash
JOBS=4 FLOW_VARIANT=run01 \
  ./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk place
```

Ket qua cua lenh tren nam trong thu muc variant `run01`.

## 7. Chay Ariane133

Ariane133 co script rieng:

```bash
JOBS=1 ./openroad_docker_lab/scripts/run_ariane133_orfs.sh
```

Ket qua:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/results/nangate45/ariane133/datn/
```

File chinh:

- `1_synth.odb`
- `2_floorplan.odb`
- `3_place.odb`
- `3_place.def`

## 8. Lien he voi dau vao RL

OpenROAD sinh `ODB/DEF`, nhung PPO hien tai doc truc tiep:

```text
netlist.pb.txt
initial.plc
```

CodeElements TILOS cu dung lenh OpenROAD `partition_design` de chuyen DEF sang
hypergraph va Protocol Buffer. Lenh nay khong con trong OpenROAD moi cua image.
Vi vay, de train Ariane133 ngay, dung bo benchmark da co:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
```

Sau do tren may GPU:

```bash
source rl_env/bin/activate

EPISODES=10 ROLLOUT_EPISODES=2 BATCH_SIZE=1 MAX_EDGES=4000 \
  ./rl_macroplacement_agent/scripts/run_ariane133_ppo.sh
```

## 9. Loi thuong gap

### Khong tim thay Docker image

```bash
./openroad_docker_lab/scripts/build.sh
```

### `DESIGN_NAME` khong ton tai

Kiem tra ten module top trong Verilog co trung voi `DESIGN_NAME` hay khong.

### Khong tim thay port clock

Sua `[get_ports clk]` trong SDC thanh ten port clock that.

### Thieu LEF hoac Liberty cua macro

Khai bao `ADDITIONAL_LEFS` va `ADDITIONAL_LIBS` trong `config.mk`.

### Muon chay lai tu dau

Doi `FLOW_VARIANT` de tao thu muc ket qua moi:

```bash
FLOW_VARIANT=run02 \
  ./openroad_docker_lab/scripts/run_orfs_design.sh \
  designs/nangate45/adder_demo/config.mk synth
```
