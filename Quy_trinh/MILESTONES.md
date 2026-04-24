# Chương 1 - Lộ Trình Triển Khai Hướng 1

Hướng 1 không còn được hiểu là cố chạy lại Google AlphaChip đầy đủ.

Hướng đúng của chương này là:

```text
OpenROAD / ORFS / Yosys
+ MacroPlacement dataset
+ plc_client_os / PlacementCost
+ Gymnasium + Stable-Baselines3
+ OpenROAD evaluation
```

Mục tiêu của toàn chương:

- dựng nền EDA open-source thay cho flow thương mại
- chuẩn hóa dữ liệu macro placement theo format `circuit_training`
- xây RL loop open-source thay cho phần RL/cost engine không public của AlphaChip
- đưa placement sinh ra quay lại OpenROAD để refine và đánh giá vật lý

## Milestone 1 - Dựng nền EDA open-source

File chi tiết:

- [MILESTONE_1.md](/home/DATN/Quy_trinh/MILESTONE_1.md)

Mục tiêu:

- dựng `OpenROAD`, `OpenROAD-flow-scripts`, `Yosys`
- chạy được baseline physical design
- sinh artifact implementation thật

Đầu ra chính:

- `1_synth.*`
- `2_floorplan.*`
- `3_place.*`
- `6_final.*`

## Milestone 2 - Chuẩn hóa dữ liệu cho RL macro placement

File chi tiết:

- [MILESTONE_2.md](/home/DATN/Quy_trinh/MILESTONE_2.md)

Mục tiêu:

- chọn benchmark có macro thật
- dùng `MacroPlacement` để lấy `netlist.pb.txt`, `initial.plc`, `legalized.plc`
- kiểm tra dữ liệu bằng `PlacementCost`

Đầu ra chính:

- `dataset_inspect.json`
- `initial.json`
- `legalized.json`

## Milestone 3 - Xây RL loop open-source thay thế AlphaChip

File chi tiết:

- [MILESTONE_3.md](/home/DATN/Quy_trinh/MILESTONE_3.md)

Mục tiêu:

- không chạy AlphaChip full
- dùng `plc_client_os` làm proxy evaluator
- dùng `Gymnasium + SB3 + MaskablePPO`
- sinh placement tốt nhất dạng `.plc`

Đầu ra chính:

- `reward_history.csv`
- `best_rl.plc`
- `best_proxy.json`
- `maskable_ppo_model.zip`

## Milestone 4 - Đưa placement quay lại OpenROAD

File chi tiết:

- [MILESTONE_4.md](/home/DATN/Quy_trinh/MILESTONE_4.md)

Mục tiêu:

- convert `best_rl.plc` sang Tcl/OpenROAD placement
- nạp vào OpenROAD
- refine, place, route nếu có thể
- đối chiếu proxy cost và QoR vật lý

Đầu ra chính:

- placement Tcl cho OpenROAD
- checkpoint/report vật lý
- bảng so sánh proxy cost và physical QoR

## Kết luận của chương

Chương 1 bây giờ phải được hiểu như sau:

```text
Không tái tạo AlphaChip đầy đủ.
Xây một flow nghiên cứu open-source tương tự AlphaChip ở mức thực nghiệm.
```
