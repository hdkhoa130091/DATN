# Example Designs

Thư mục `example/` chứa các RTL nhỏ để thử pipeline trong repo.

## Mục đích từng ví dụ

- `simple_sram.v`
  - ví dụ bộ nhớ suy diễn
  - không phù hợp để chạy macro-placement RL vì sau tổng hợp nó không tạo ra tập hard macro di động đúng kiểu mà `flow.py` và RL hiện tại đang cần

- `simple_cpu.v`
  - ví dụ logic tuần tự nhỏ
  - phù hợp để thử tổng hợp RTL cơ bản, nhưng không phải ví dụ tốt cho macro-placement RL nếu không có hard macro rõ ràng

- `soc_top.v`
  - ví dụ top-level nhỏ ghép nhiều khối
  - hữu ích để thử synth/EDA cơ bản

- `macro_cluster_demo.v`
  - ví dụ phù hợp nhất để đi hết chuỗi:
    - RTL
    - ORFS synthesis
    - floorplan
    - placement ban đầu
    - chuẩn bị input cho `flow.py`
    - sinh `netlist.pb.txt` và `initial.plc`
    - chạy PPO smoke test
  - ví dụ này cố tình dùng 4 instance `fakeram45_256x16` để tạo hard macro thật sự cho pipeline macro-placement

- `practical_macro_soc.v`
  - ví dụ “gần thực tế” hơn cho macro-placement RL
  - dùng 8 hard macro SRAM giả lập:
    - 2 instruction memories
    - 2 data memories
    - 2 DMA buffers
    - 2 IO buffers
  - có logic điều khiển và kết nối chéo giữa nhiều macro nên phù hợp hơn để thử tác động của placement

## Pipeline khả thi hiện tại

Ví dụ khả thi nhất trong repo hiện tại để đi trọn chuỗi EDA -> `flow.py` -> RL là:

```text
example/macro_cluster_demo.v
```

Ví dụ nên thử tiếp theo nếu bạn muốn một top-level gần ứng dụng hơn:

```text
example/practical_macro_soc.v
```

Script orchestration:

```bash
./openroad_docker_lab/scripts/run_demo_pipeline.sh
```

Nếu muốn chạy thêm RL smoke test ở cuối:

```bash
RUN_RL=1 ./openroad_docker_lab/scripts/run_demo_pipeline.sh
```

## Vì sao `simple_sram.v` không phù hợp cho RL hiện tại

RL hiện tại trong `rl_macroplacement_agent/` không học trên mọi netlist số nói chung. Nó giả định đầu vào sau `flow.py` phải chứa:

- hard macro di động
- graph và feature đúng kiểu MacroPlacement
- `initial.plc` có macro để agent lần lượt đặt

`simple_sram.v` là memory inference RTL. Với flow hiện tại, nó không cho ra dataset macro-placement phù hợp như các testcase kiểu `ariane133` hay `macro_cluster_demo`.

## Cách thử `practical_macro_soc`

### 1. Cài design vào ORFS

```bash
cd /workspace/DATN
./openroad_docker_lab/scripts/setup_practical.sh
```

### 2. Chạy synthesis

```bash
cd /workspace/DATN
FLOW_VARIANT=practical_run_01 \
./openroad_docker_lab/scripts/run_orfs.sh \
designs/nangate45/practical_macro_soc/config.mk synth
```

### 3. Chạy floorplan

```bash
cd /workspace/DATN
FLOW_VARIANT=practical_run_01 \
./openroad_docker_lab/scripts/run_orfs.sh \
designs/nangate45/practical_macro_soc/config.mk floorplan
```

### 4. Chạy placement

```bash
cd /workspace/DATN
FLOW_VARIANT=practical_run_01 \
./openroad_docker_lab/scripts/run_orfs.sh \
designs/nangate45/practical_macro_soc/config.mk place
```

### 5. Export input cho `flow.py`

```bash
cd /workspace/DATN
./openroad_docker_lab/scripts/export_flow_inputs.sh \
  nangate45 practical_macro_soc practical_run_01 practical_macro_soc_orfs
```

### 6. Chạy `flow.py`

```bash
cd /workspace/DATN
python3 MacroPlacement/Flows/util/flow.py \
  MacroPlacement/Flows/NanGate45/generated/practical_macro_soc/practical_macro_soc_orfs \
  MacroPlacement/Flows/NanGate45/generated/practical_macro_soc/practical_macro_soc_orfs/output_CodeElement
```

### 7. Kiểm tra dataset

```bash
cd /workspace/DATN
python3 rl_macroplacement_agent/scripts/inspect_dataset.py \
  --netlist MacroPlacement/Flows/NanGate45/generated/practical_macro_soc/practical_macro_soc_orfs/practical_macro_soc.pb.txt \
  --initial_plc MacroPlacement/Flows/NanGate45/generated/practical_macro_soc/practical_macro_soc_orfs/practical_macro_soc.plc
```

### 8. PPO smoke test

```bash
cd /workspace/DATN
python3 rl_macroplacement_agent/scripts/train_ppo.py \
  --netlist MacroPlacement/Flows/NanGate45/generated/practical_macro_soc/practical_macro_soc_orfs/practical_macro_soc.pb.txt \
  --init_plc MacroPlacement/Flows/NanGate45/generated/practical_macro_soc/practical_macro_soc_orfs/practical_macro_soc.plc \
  --out_dir experiments/practical_macro_soc_smoke \
  --episodes 5 \
  --rollout_episodes 2 \
  --max_macros 8 \
  --max_nodes 2048 \
  --max_edges 6000 \
  --max_grid 32 \
  --batch_size 1 \
  --device cuda
```

## Tiêu chí để xem ví dụ này có khả thi

`practical_macro_soc` được xem là khả thi nếu:

1. ORFS synth không lỗi
2. ORFS floorplan/place giữ được 8 hard macro
3. `flow.py` sinh được `.pb.txt` và `.plc`
4. PPO smoke test chạy được
