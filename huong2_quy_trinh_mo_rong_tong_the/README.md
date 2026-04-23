# Quy Trình Tổng Thể Theo Chiều Sâu

Tài liệu này mô tả cách triển khai đầy đủ hơn về mặt nghiên cứu. Mục tiêu không chỉ là chạy được pipeline EDA + học tăng cường, mà còn hiểu và mô tả được toàn bộ quá trình hình thành dữ liệu, biến đổi dữ liệu và đánh giá kết quả.

Trong hướng này cần làm rõ:

- testcase được xây từ đâu
- mã RTL hoặc netlist ban đầu được tổng hợp như thế nào
- các file `Verilog`, netlist gate-level, `LEF`, `DEF`, `SDC`, `SPEF` được sinh ra ở bước nào
- dữ liệu được chuyển thành đầu vào cho học tăng cường ra sao
- kết quả placement từ RL được đưa ngược lại EDA như thế nào

Cách tiếp cận này phù hợp khi mục tiêu chính là:

- hiểu sâu bản chất của pipeline macroplacement
- giải thích được nguồn gốc của từng nhóm dữ liệu
- có khả năng tái tạo, mở rộng hoặc thay thế từng khâu trong pipeline

Các giai đoạn chính:

- [MILESTONE_1.md](/home/DATN/huong2_quy_trinh_mo_rong_tong_the/MILESTONE_1.md): làm rõ nền EDA, testcase và nguồn gốc của artifact
- [MILESTONE_2.md](/home/DATN/huong2_quy_trinh_mo_rong_tong_the/MILESTONE_2.md): phân tích sâu luồng chuyển đổi dữ liệu từ EDA sang RL
- [MILESTONE_3.md](/home/DATN/huong2_quy_trinh_mo_rong_tong_the/MILESTONE_3.md): mô tả và kiểm soát state, action, reward, environment
- [MILESTONE_4.md](/home/DATN/huong2_quy_trinh_mo_rong_tong_the/MILESTONE_4.md): đưa kết quả RL quay lại EDA để refine và đánh giá
