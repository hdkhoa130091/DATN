# Các Giai Đoạn Nghiên Cứu Chuyên Sâu

## Giai đoạn làm rõ nền EDA và nguồn gốc artifact

- làm rõ testcase, thư viện công nghệ và chuỗi tạo artifact EDA
- xác định nguồn gốc của `Verilog`, netlist, `LEF`, `DEF`, `SDC`, `SPEF`
- chạy flow mẫu để đối chiếu giữa lý thuyết và kết quả thực

## Giai đoạn phân tích luồng chuyển đổi dữ liệu

- phân tích luồng chuyển đổi dữ liệu từ artifact EDA sang dữ liệu dùng cho RL
- làm rõ cách các công cụ hiện có biểu diễn macro, pin, port, connectivity và placement
- xác định các khối dữ liệu cần cho state, action, reward và placement cost

## Giai đoạn mô tả environment và cơ chế tối ưu

- mô tả sâu environment RL cho macroplacement
- làm rõ state, action, reward và cách chúng liên hệ với chất lượng placement
- chạy baseline để quan sát hành vi của pipeline

## Giai đoạn đưa kết quả quay lại EDA

- đưa placement từ RL quay lại flow EDA
- refine và đánh giá lại bằng chỉ số vật lý
- so sánh với quy trình triển khai thực dụng và tổng hợp kết luận nghiên cứu
