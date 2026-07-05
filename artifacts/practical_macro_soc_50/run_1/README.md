# `practical_macro_soc_50` `run_1` Artifacts

Thư mục này lưu bộ artifact đã chạy sẵn cho workflow `practical_macro_soc_50` với
`FLOW_VARIANT=run_1`.

## Nội dung

- `train/`
  - `alphachip_like_actor_critic.pt`: model sau khi train
  - `alphachip_like_train_summary.json`: tóm tắt train
  - `alphachip_like_training_history.csv`: lịch sử train theo từng episode
- `eval/`
  - `alphachip_like_eval_summary.json`: tóm tắt evaluation
  - `alphachip_like_final.plc`: placement cuối do policy sinh ra
  - `final_from_plc.tcl`: Tcl convert từ `alphachip_like_final.plc`
  - `final_from_plc_clamped.tcl`: Tcl đã clamp vào core
- `macroplacement_input/`
  - `practical_macro_soc_50.pb.txt`: đầu vào graph cho RL
  - `practical_macro_soc_50.plc`: initial placement sau `flow.py`
- `openroad/`
  - `3_place.def`: placement DEF gốc từ ORFS
  - `rl_placed.def`: DEF sau khi source kết quả RL vào OpenROAD

## Mục đích

Bộ artifact này cho phép:

- đối chiếu kết quả train/eval mà không cần chạy lại từ đầu
- mở kết quả RL trên OpenROAD bằng `final_from_plc_clamped.tcl`
- tiếp tục các bước backend như CTS từ placement đã được RL cập nhật

## Không bao gồm

- các file `.odb` lớn
- toàn bộ log ORFS trung gian
- toàn bộ thư mục `generated/` và `results/`

Nếu cần tái hiện full pipeline, hãy dùng [Huong_dan_Pipeline.md](../../../Huong_dan_Pipeline.md).
