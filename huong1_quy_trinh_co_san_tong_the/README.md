# Quy Trình Tổng Thể Bằng Công Cụ Có Sẵn

Tài liệu này mô tả cách triển khai thực dụng, ưu tiên dùng những công cụ và workflow đã có sẵn để dựng nhanh một pipeline EDA + học tăng cường có thể chạy được, quan sát được và cho ra kết quả.

Trong hướng này, trọng tâm không nằm ở việc tự tái tạo mọi thành phần từ đầu, mà nằm ở việc:

- dựng được flow EDA open-source ổn định
- chọn được benchmark có macro
- chuyển dữ liệu sang pipeline RL bằng công cụ có sẵn
- chạy được baseline placement hoặc học tăng cường
- lưu kết quả và quan sát lại bằng phần mềm phù hợp

Hướng tiếp cận này phù hợp khi mục tiêu chính là:

- có baseline triển khai sớm
- có demo hoặc kết quả để đối chiếu
- bám sát hệ sinh thái `OpenROAD`, `MacroPlacement`, `circuit_training`

Các giai đoạn chính:

- [MILESTONE_1.md](/home/DATN/huong1_quy_trinh_co_san_tong_the/MILESTONE_1.md): dựng nền EDA open-source và sinh artifact vật lý đầu tiên
- [MILESTONE_2.md](/home/DATN/huong1_quy_trinh_co_san_tong_the/MILESTONE_2.md): dùng công cụ có sẵn để đưa dữ liệu thiết kế sang pipeline RL
- [MILESTONE_3.md](/home/DATN/huong1_quy_trinh_co_san_tong_the/MILESTONE_3.md): chạy baseline placement hoặc học tăng cường và ghi nhận kết quả
- giai đoạn tiếp theo: đưa placement quay lại EDA để refine, đo QoR và tổng hợp kết quả nghiên cứu
