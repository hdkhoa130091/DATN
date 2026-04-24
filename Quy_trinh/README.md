# Hướng 1 - Quy Trình Tổng Thể Bằng Công Cụ Open-Source

Thư mục này mô tả hướng triển khai chính của đồ án theo flow open-source thay thế cho hướng AlphaChip không thể chạy đầy đủ trong môi trường hiện tại.

Điểm quan trọng nhất của hướng 1 là:

```text
Không cố chạy Google AlphaChip full system.
Thay vào đó, xây một pipeline open-source tương tự ở mức nghiên cứu.
```

Flow tổng thể:

```text
OpenROAD / ORFS / Yosys
    -> tạo nền EDA và backend vật lý

MacroPlacement dataset
    -> cung cấp benchmark có macro thật
    -> netlist.pb.txt + initial.plc + legalized.plc

plc_client_os / PlacementCost
    -> proxy evaluator cho RL

Gymnasium + Stable-Baselines3 + MaskablePPO
    -> RL loop open-source thay phần AlphaChip RL infra

best_rl.plc
    -> convert sang OpenROAD Tcl
    -> đưa lại vào OpenROAD để refine và đánh giá QoR
```

## Thành phần thay thế chính

- `Genus` -> `Yosys`
- `Innovus` -> `OpenROAD` và `OpenROAD-flow-scripts`
- `plc_wrapper_main` -> `plc_client_os`
- AlphaChip RL infrastructure -> `Gymnasium`, `stable-baselines3`, `sb3-contrib`

## Các mốc chính

- [MILESTONE_1.md](/home/DATN/Quy_trinh/MILESTONE_1.md)
  dựng nền EDA open-source và sinh artifact vật lý
- [MILESTONE_2.md](/home/DATN/Quy_trinh/MILESTONE_2.md)
  chuẩn hóa dữ liệu macro placement cho RL
- [MILESTONE_3.md](/home/DATN/Quy_trinh/MILESTONE_3.md)
  xây RL loop open-source thay thế AlphaChip
- [MILESTONE_4.md](/home/DATN/Quy_trinh/MILESTONE_4.md)
  đưa placement quay lại OpenROAD để đánh giá vật lý

## Trạng thái hiểu đúng của hướng 1

Hướng 1 không phải là:

- rebuild toàn bộ AlphaChip của Google
- phụ thuộc `plc_wrapper_main`
- phụ thuộc backend Google internal

Hướng 1 là:

- dùng dataset `MacroPlacement`
- dùng `PlacementCost` làm proxy cost
- dùng PPO/MaskablePPO để học tăng cường
- dùng OpenROAD để kiểm chứng giá trị vật lý của placement đầu ra

## Điểm khởi đầu nên dùng

Benchmark đầu tiên:

```bash
/home/DATN/MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

Project code mới:

```bash
/home/DATN/rl_macroplacement_agent
```

## Tài liệu gốc tham chiếu

Nếu cần xem bản mô tả chi tiết flow thay thế, đọc:

- [AGENT_RL_MACROPLACEMENT_OPEN_SOURCE_FLOW.md](/home/DATN/AGENT_RL_MACROPLACEMENT_OPEN_SOURCE_FLOW.md)
