# Milestone 4 - Đưa Placement Từ RL Quay Lại OpenROAD

## Mục tiêu

Milestone 4 có nhiệm vụ khép kín vòng lặp nghiên cứu:

```text
EDA -> data chuẩn hóa -> RL placement -> quay lại EDA để đánh giá
```

Mục tiêu của milestone này là:

- lấy `best_rl.plc` từ milestone 3
- convert sang dạng placement mà OpenROAD đọc được
- chạy lại placement/refine/evaluate
- đối chiếu proxy cost với QoR vật lý

## Vai trò của milestone 4

Nếu milestone 3 trả lời câu hỏi:

```text
RL loop có chạy được không?
```

thì milestone 4 trả lời:

```text
placement đầu ra có dùng lại được trong flow vật lý không?
```

## Công cụ sử dụng

- `OpenROAD`
- `OpenROAD-flow-scripts`
- `plc_pb_to_placement_tcl.py`
- script chuyển đổi Tcl cho OpenROAD
- `PlacementCost` để đối chiếu proxy

## Kiến trúc milestone 4

```text
best_rl.plc
    -> convert sang Tcl placement
    -> OpenROAD load placement
    -> refine / place / route
    -> report vật lý
    -> compare với proxy cost
```

## File chính của milestone 4

- `plc_to_openroad_tcl.py`
- `run_openroad_eval.sh`
- `compare_results.py`
- `compare_summary.md`

## Quy trình thực hiện

### 1. Convert `.plc` sang Tcl

Script có sẵn:

```bash
python3 /home/DATN/MacroPlacement/Flows/util/plc_pb_to_placement_tcl.py \
  /home/DATN/rl_macroplacement_agent/results/ppo/ariane133_ng45/best_rl.plc \
  /home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/netlist.pb.txt \
  /home/DATN/rl_macroplacement_agent/results/openroad/ariane133_ng45/best_rl_macro_place_raw.tcl
```

### 2. Chuyển Tcl sang cú pháp OpenROAD nếu cần

Mục tiêu là có file như:

```text
best_rl_macro_place_openroad.tcl
```

### 3. Nạp placement vào OpenROAD

Nếu ORFS/design config hỗ trợ biến placement Tcl:

```bash
export MACRO_PLACEMENT_TCL=/home/DATN/rl_macroplacement_agent/results/openroad/ariane133_ng45/best_rl_macro_place_openroad.tcl
```

Sau đó chạy flow OpenROAD với testcase macro tương ứng.

## Điều quan trọng

Không ép testcase `gcd` vào macro placement.

Phải dùng testcase macro thật như `ariane133` hoặc testcase tương ứng trong `MacroPlacement`.

## Chỉ số cần so sánh

- proxy cost
- wirelength
- density
- congestion nếu ổn định
- route success
- timing slack nếu có
- runtime

## Tiêu chí hoàn thành

Mức tối thiểu:

- `best_rl.plc` convert được sang Tcl
- OpenROAD đọc được placement Tcl

Mức tốt:

- flow đi qua floorplan/place hoặc refine
- có report hoặc checkpoint

Mức rất tốt:

- route được
- có so sánh giữa proxy cost và QoR vật lý

## Kết luận cần rút ra

Milestone 4 không nhằm chứng minh flow open-source tương đương hoàn toàn với AlphaChip của Google.

Milestone 4 nhằm chứng minh rằng:

- có thể xây một pipeline nghiên cứu macro placement tương tự AlphaChip ở mức thực nghiệm
- placement đầu ra từ RL có thể được kiểm chứng bằng backend vật lý open-source
