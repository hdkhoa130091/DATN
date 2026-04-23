# Nền EDA, Testcase Và Nguồn Gốc Artifact

## Mục tiêu

Tài liệu này tập trung vào việc hiểu và dựng đầy đủ nền EDA tạo ra testcase và artifact phục vụ nghiên cứu macroplacement.

Ở giai đoạn này không chỉ dừng ở việc chạy được flow, mà còn phải làm rõ:

- testcase đến từ đâu
- RTL hoặc netlist ban đầu có dạng gì
- thư viện công nghệ nào tham gia vào flow
- các bước tổng hợp và physical design sinh ra những file nào

## Nội dung chính

- chuẩn bị môi trường EDA open-source
- xác định chuỗi đầu vào từ RTL, netlist, thư viện công nghệ đến constraint
- làm rõ vai trò của `Verilog`, netlist gate-level, `LEF`, `DEF`, `SDC`, `SPEF`
- chạy một flow mẫu để đối chiếu giữa lý thuyết và artifact thực tế

## Đầu vào

- mã RTL hoặc testcase có sẵn
- thư viện công nghệ
- tool synthesis và physical design
- các ràng buộc thiết kế

## Đầu ra

- flow EDA có thể chạy được
- hiểu rõ nguồn gốc và ý nghĩa của các artifact chính
- xác định được chuỗi biến đổi dữ liệu từ mô tả thiết kế sang implementation

## Tiêu chí hoàn thành

- giải thích được từng nhóm file chính trong testcase
- chạy được flow mẫu để kiểm chứng
- xác định được artifact nào sẽ được dùng tiếp ở các bước sau
