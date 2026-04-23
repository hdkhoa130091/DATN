# Các Giai Đoạn Triển Khai

## Giai đoạn dựng nền EDA

- dựng được flow EDA open-source thay cho Genus và Innovus
- sinh được artifact vật lý ổn định để dùng tiếp cho các bước sau
- có thể quan sát checkpoint và kết quả bằng GUI hoặc VNC khi cần

## Giai đoạn chuẩn hóa dữ liệu cho RL

- chọn benchmark có macro thật thay vì chỉ dùng testcase kiểm tra flow
- dùng công cụ có sẵn để chuyển dữ liệu thiết kế sang pipeline RL
- kiểm tra dữ liệu đầu ra bằng công cụ đánh giá placement hiện có

## Giai đoạn chạy baseline placement hoặc RL

- nối dữ liệu đã chuẩn hóa vào environment hoặc RL loop có sẵn
- chạy được baseline placement hoặc học tăng cường
- lưu được kết quả placement, reward và log để phân tích

## Giai đoạn refine và đánh giá lại bằng EDA

- đưa placement đầu ra quay lại EDA để refine
- đo lại chỉ số vật lý và đối chiếu với proxy cost
- tổng hợp kết quả làm baseline ứng dụng của đề tài
