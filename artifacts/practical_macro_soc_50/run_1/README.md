# `practical_macro_soc_50` `run_1` Artifacts

Thu muc nay luu bo artifact da chay san cho workflow `practical_macro_soc_50` voi
`FLOW_VARIANT=run_1`.

## Noi dung

- `train/`
  - `alphachip_like_actor_critic.pt`: model sau khi train
  - `alphachip_like_train_summary.json`: tom tat train
  - `alphachip_like_training_history.csv`: lich su train theo episode
- `eval/`
  - `alphachip_like_eval_summary.json`: tom tat evaluation
  - `alphachip_like_final.plc`: placement cuoi do policy sinh ra
  - `final_from_plc.tcl`: Tcl convert tu `alphachip_like_final.plc`
  - `final_from_plc_clamped.tcl`: Tcl da clamp vao core
- `macroplacement_input/`
  - `practical_macro_soc_50.pb.txt`: dau vao graph cho RL
  - `practical_macro_soc_50.plc`: initial placement sau `flow.py`
- `openroad/`
  - `3_place.def`: placement DEF goc tu ORFS
  - `rl_placed.def`: DEF sau khi source ket qua RL vao OpenROAD

## Muc dich

Bo artifact nay cho phep:

- doi chieu ket qua train/eval ma khong can chay lai tu dau
- mo ket qua RL tren OpenROAD bang `final_from_plc_clamped.tcl`
- tiep tuc cac buoc backend nhu CTS tu placement da duoc RL cap nhat

## Khong bao gom

- cac file `.odb` lon
- toan bo log ORFS trung gian
- toan bo thu muc `generated/` va `results/`

Neu can tai hien full pipeline, hay dung `openroad_docker_lab/FULL_EDA_RL_PIPELINE.md`.
