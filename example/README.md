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

## Pipeline khả thi hiện tại

Ví dụ khả thi nhất trong repo hiện tại để đi trọn chuỗi EDA -> `flow.py` -> RL là:

```text
example/macro_cluster_demo.v
```

Script orchestration:

```bash
./openroad_docker_lab/scripts/run_macro_cluster_demo_pipeline.sh
```

Nếu muốn chạy thêm RL smoke test ở cuối:

```bash
RUN_RL=1 ./openroad_docker_lab/scripts/run_macro_cluster_demo_pipeline.sh
```

## Vì sao `simple_sram.v` không phù hợp cho RL hiện tại

RL hiện tại trong `rl_macroplacement_agent/` không học trên mọi netlist số nói chung. Nó giả định đầu vào sau `flow.py` phải chứa:

- hard macro di động
- graph và feature đúng kiểu MacroPlacement
- `initial.plc` có macro để agent lần lượt đặt

`simple_sram.v` là memory inference RTL. Với flow hiện tại, nó không cho ra dataset macro-placement phù hợp như các testcase kiểu `ariane133` hay `macro_cluster_demo`.
