# Quy trình tổng hợp RTL với Yosys và OpenROAD

## Giới thiệu

## Chuẩn bị môi trường host cho phần Python/RL

Trước khi chạy các bước `flow.py`, `fix_plc.py`, train RL hay eval RL trên host,
hãy tạo virtualenv thống nhất như sau:

```bash
cd /home/khoahd/Documents/DATN-1
python3.10 -m venv rl_env
source rl_env/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r rl_macroplacement_agent/requirements.txt
```

Nên dùng `python3.10` hoặc `python3.11`. Không nên dùng `python3.14` cho
virtualenv này vì `torch<2.5` trong pipeline hiện tại không có wheel phù hợp.

Nếu chỉ muốn kiểm tra lại môi trường đã có:

```bash
cd /home/khoahd/Documents/DATN-1
source rl_env/bin/activate
python -c "import absl, numpy, matplotlib, sortedcontainers, torch, pandas; print('python env ok')"
python rl_macroplacement_agent/scripts/train_ppo.py --help > /dev/null
python rl_macroplacement_agent/scripts/eval_policy.py --help > /dev/null
python openroad_docker_lab/scripts/fix_plc.py --help > /dev/null
echo "pipeline python scripts ok"
```

Quy trình chuẩn để tạo đầu vào cho bài toán macro placement gồm các giai đoạn:

```text
RTL Verilog (.v) -----------+
Thư viện Liberty (.lib) ----+--> Yosys + ABC
Ràng buộc timing (.sdc) ----+        |
                                     v
                         Gate-level Verilog (.v)
                         Database synthesis (.odb)
                         SDC sau synthesis (.sdc)
                                     |
LEF công nghệ và macro (.lef) -------+--> OpenROAD
                                     |
                                     v
                         Floorplan/placement (.odb, .def)
                                     |
                                     v
                         flow.py hoặc run_CodeFlow.sh
                                     |
                                     v
                         netlist.pb.txt + initial.plc
```

Ý nghĩa của từng giai đoạn:

1. **RTL Verilog** mô tả chức năng logic của thiết kế.
2. **Yosys** đọc RTL, phân cấp thiết kế, chuyển các process thành mạch logic và
   tối ưu netlist.
3. **ABC** ánh xạ logic sang các standard cell có trong thư viện Liberty của
   Nangate45.
4. **OpenROAD** đọc netlist đã tổng hợp, LEF công nghệ, LEF macro và SDC để tạo
   floorplan và placement vật lý.
5. **Code Flow** chuyển dữ liệu vật lý sang đồ thị macro placement, tạo
   `netlist.pb.txt` và `initial.plc` cho môi trường học tăng cường.

Một điểm cần phân biệt rõ:

- `.lib` và `.sdc` là đầu vào của tổng hợp và phân tích timing.
- `.lef` là đầu vào vật lý mô tả kích thước, pin và obstruction của cell/macro.
- Yosys tạo gate-level netlist `.v`.
- OpenROAD tạo database `.odb` và có thể xuất placement `.def`.
- `flow.py` hoặc `run_CodeFlow.sh` mới là bước tạo dữ liệu
  `netlist.pb.txt` và `initial.plc`.

## Script tổng quát

Script dùng cho mọi thiết kế:

```text
openroad_docker_lab/scripts/run_orfs.sh
```

Cú pháp:

```bash
./openroad_docker_lab/scripts/run_orfs.sh \
  <đường-dẫn-config.mk> [synth|floorplan|place]
```

Đường dẫn `config.mk` được tính tương đối từ:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
```

Các stage được hỗ trợ:

| Stage | Công việc được thực hiện | Đầu ra chính |
|---|---|---|
| `synth` | Tổng hợp RTL và ánh xạ standard cell | `1_2_yosys.v`, `1_synth.odb`, `1_synth.sdc` |
| `floorplan` | Chạy synthesis, sau đó tạo floorplan | `2_floorplan.odb` |
| `place` | Chạy synthesis, floorplan và placement | `3_place.odb` |

Nếu không truyền stage, script mặc định chạy `synth`.

Các biến môi trường có thể cấu hình:

```text
JOBS             Số tiến trình make chạy song song, mặc định là 1
FLOW_VARIANT     Tên lần chạy và thư mục kết quả, mặc định là datn
CONTAINER_NAME   Tên container, mặc định là openroad_cli
IMAGE_NAME       Tên Docker image, mặc định là openroad-docker-lab:latest
```

Ví dụ:

```bash
JOBS=4 FLOW_VARIANT=run_01 \
  ./openroad_docker_lab/scripts/run_orfs.sh \
  designs/nangate45/adder_demo/config.mk place
```

## Các file đầu vào

Một testcase ORFS thường có cấu trúc:

```text
flow/
├── designs/
│   ├── src/
│   │   └── <tên-thiết-kế>/
│   │       └── <top-module>.v
│   └── nangate45/
│       └── <tên-thiết-kế>/
│           ├── config.mk
│           ├── constraint.sdc
│           ├── macros.v
│           ├── memory.lef
│           └── memory.lib
```

Các file bắt buộc hoặc thường dùng:

### RTL Verilog

File `.v` chứa module top và các module con:

```verilog
module adder_demo (
    input  wire       clk,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [7:0] sum
);
  always @(posedge clk) begin
    sum <= a + b;
  end
endmodule
```

Tên module top phải trùng với `DESIGN_NAME` trong `config.mk`.

### `config.mk`

`config.mk` mô tả thiết kế, platform và các file đầu vào:

```make
export DESIGN_NAME = adder_demo
export DESIGN_NICKNAME = adder_demo
export PLATFORM = nangate45

export VERILOG_FILES = \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/adder_demo.v

export SDC_FILE = \
  $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

export CORE_UTILIZATION = 50
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 5
export ABC_AREA = 1
```

Nếu thiết kế có nhiều file RTL:

```make
export VERILOG_FILES = \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/top.v \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/alu.v \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/control.v
```

Nếu thiết kế có SRAM hoặc hard macro:

```make
export VERILOG_FILES = \
  $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/top.v \
  $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/macros.v

export ADDITIONAL_LEFS = \
  $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/memory.lef

export ADDITIONAL_LIBS = \
  $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/memory.lib
```

Trong đó:

- `macros.v` khai báo giao diện logic của macro.
- `memory.lef` mô tả hình học vật lý và vị trí pin.
- `memory.lib` mô tả timing, công suất và chức năng logic.

### `constraint.sdc`

Ví dụ clock chu kỳ 10 ns, tương ứng 100 MHz:

```tcl
create_clock -name core_clock -period 10.0 [get_ports clk]
```

Tên `clk` phải trùng với clock port của module top. Một thiết kế thực tế có thể
cần thêm:

```tcl
set_input_delay  1.0 -clock core_clock [get_ports data_in]
set_output_delay 1.0 -clock core_clock [get_ports data_out]
set_clock_uncertainty 0.1 [get_clocks core_clock]
```

## Chạy synthesis

Cú pháp:

```bash
./openroad_docker_lab/scripts/run_orfs.sh \
  designs/nangate45/adder_demo/config.mk synth
```

Script thực hiện:

```text
Đọc RTL và Liberty
-> xác định module top
-> chuyển process thành logic
-> tối ưu FSM, memory và biểu thức
-> ánh xạ flip-flop theo Liberty
-> ABC ánh xạ logic sang Nangate45
-> ghi gate-level Verilog
-> tạo OpenROAD database
```

Lệnh ORFS tương ứng:

```bash
make DESIGN_CONFIG=designs/nangate45/adder_demo/config.mk \
  FLOW_VARIANT=datn synth
```

ORFS sử dụng thư mục nội bộ sau để truyền dữ liệu giữa các stage:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  results/<platform>/<design>/<flow-variant>/
```

Không đổi tên hoặc xóa thư mục `results/` khi đang chạy flow vì floorplan cần
đọc kết quả synthesis và placement cần đọc kết quả floorplan.

Script `run_orfs.sh` đồng thời xuất kết quả từng stage sang các thư mục
dễ nhận biết hơn:

```text
SynthesisResults/<platform>/<design>/<flow-variant>/
FloorplanningResults/<platform>/<design>/<flow-variant>/
PlacementResults/<platform>/<design>/<flow-variant>/
```

Trong đó:

- `<platform>` lấy từ biến `PLATFORM` trong `config.mk`, ví dụ `nangate45`.
- `<design>` thường lấy từ `DESIGN_NICKNAME`, ví dụ `adder_demo`.
- `<flow-variant>` lấy từ biến môi trường `FLOW_VARIANT`; nếu không đặt thì
  script sử dụng giá trị mặc định `datn`.

Với lệnh `adder_demo` phía trên, kết quả synthesis được xuất tại:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  SynthesisResults/nangate45/adder_demo/datn/
```

Ví dụ, nếu testcase là `mempool`, platform là `nangate45` và không thay đổi
`FLOW_VARIANT`, kết quả synthesis nằm tại:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  SynthesisResults/nangate45/mempool/datn/
```

Các đầu ra quan trọng:

```text
1_2_yosys.v    Netlist gate-level đã ánh xạ sang standard cell Nangate45
1_synth.odb    Database tổng hợp để OpenROAD tiếp tục xử lý
1_synth.sdc    Ràng buộc timing dùng cho các stage vật lý
```

Log tổng hợp:

```text
openroad_docker_lab/OpenROAD-flow-scripts/flow/
  logs/<platform>/<design>/<flow-variant>/1_2_yosys.log
```

## Chạy floorplan

Cú pháp:

```bash
./openroad_docker_lab/scripts/run_orfs.sh \
  designs/nangate45/adder_demo/config.mk floorplan
```

Script chạy lần lượt:

```text
make ... synth
make ... do-floorplan
```

Đầu ra chính:

```text
FloorplanningResults/<platform>/<design>/<flow-variant>/2_floorplan.odb
```

Database này chứa die/core area, placement rows, tracks, vị trí I/O, vị trí
macro, tap cell và cấu hình mạng nguồn.

## Chạy placement

Cú pháp:

```bash
./openroad_docker_lab/scripts/run_orfs.sh \
  designs/nangate45/adder_demo/config.mk place
```

Script chạy lần lượt:

```text
make ... synth
make ... do-floorplan
make ... do-place
```

Đầu ra chính:

```text
PlacementResults/<platform>/<design>/<flow-variant>/3_place.odb
```

Stage placement gồm global placement, I/O placement, timing-driven resizing và
detailed placement.

## Tạo `netlist.pb.txt` và `initial.plc`

Sau synthesis và physical design, Code Flow cần một run directory có các file
vật lý và file thiết lập phù hợp. Giao diện Python là:

```bash
python MacroPlacement/Flows/util/flow.py \
  <run-directory> <output-directory>
```

Hoặc chạy wrapper trong run directory:

```bash
export PHY_SYNTH=1
MacroPlacement/Flows/util/run_CodeFlow.sh
```

Các bước chính của Code Flow:

```text
DEF + gate-level netlist + LEF
-> gridding
-> grouping
-> hypergraph clustering
-> soft-macro netlist
-> netlist.pb.txt + initial.plc
```

`netlist.pb.txt` chứa đồ thị kết nối, macro, macro pin, port và soft macro.
`initial.plc` chứa kích thước canvas, lưới placement, tọa độ và orientation; tùy
phiên bản Code Flow, phần đầu file có thể kèm các chỉ số proxy như wirelength,
congestion và density.

Code Flow TILOS hiện dùng lệnh OpenROAD cũ `partition_design`. Vì vậy cần dùng
đúng phiên bản OpenROAD tương thích với CodeElements khi muốn tạo lại hai file
này từ DEF.

## Ví dụ cuối: tổng hợp Ariane133 cho luồng DreamPlace/macro placement

Bộ đầu vào Ariane133 có sẵn tại:

```text
MacroPlacement/Flows/NanGate45/ariane133/scripts/OpenROAD/ariane133/
```

Các file chính:

```text
ariane.v                    RTL Verilog của thiết kế Ariane
config.mk                   Cấu hình ORFS và Nangate45
constraint.sdc              Clock và các ràng buộc timing
macros.v                    Khai báo logic của SRAM macro
fakeram45_256x16.lef        Hình học vật lý của SRAM
fakeram45_256x16.lib        Timing và chức năng của SRAM
```

Chép testcase Ariane vào cây thiết kế của ORFS:

```bash
FLOW=openroad_docker_lab/OpenROAD-flow-scripts/flow
SRC=MacroPlacement/Flows/NanGate45/ariane133/scripts/OpenROAD/ariane133

mkdir -p "$FLOW/designs/nangate45/ariane133"
cp "$SRC/ariane.v" "$FLOW/designs/nangate45/ariane133/"
cp "$SRC/config.mk" "$FLOW/designs/nangate45/ariane133/"
cp "$SRC/constraint.sdc" "$FLOW/designs/nangate45/ariane133/"
cp "$SRC/macros.v" "$FLOW/designs/nangate45/ariane133/"
cp "$SRC/fakeram45_256x16.lef" "$FLOW/designs/nangate45/ariane133/"
cp "$SRC/fakeram45_256x16.lib" "$FLOW/designs/nangate45/ariane133/"
```

Chạy riêng synthesis:

```bash
JOBS=1 FLOW_VARIANT=ariane_synth \
  ./openroad_docker_lab/scripts/run_orfs.sh \
  designs/nangate45/ariane133/config.mk synth
```

Chạy đến placement:

```bash
JOBS=1 FLOW_VARIANT=ariane_place \
  ./openroad_docker_lab/scripts/run_orfs.sh \
  designs/nangate45/ariane133/config.mk place
```

Kết quả synthesis:

```text
SynthesisResults/nangate45/ariane133/ariane_synth/1_2_yosys.v
SynthesisResults/nangate45/ariane133/ariane_synth/1_synth.odb
SynthesisResults/nangate45/ariane133/ariane_synth/1_synth.sdc
```

Kết quả placement:

```text
FloorplanningResults/nangate45/ariane133/ariane_place/2_floorplan.odb
PlacementResults/nangate45/ariane133/ariane_place/3_place.odb
```

Đầu vào macro placement/RL đã được tạo sẵn tại:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/initial.plc
```
