# Luồng Chuyển Đổi Dữ Liệu Từ EDA Sang RL

## Mục tiêu

Tài liệu này tập trung vào việc phân tích sâu cách dữ liệu EDA được chuyển hóa thành dữ liệu mà bài toán học tăng cường có thể sử dụng.

Trọng tâm của giai đoạn này là làm rõ:

- dữ liệu nào được trích từ testcase và artifact EDA
- vì sao phải chuẩn hóa dữ liệu trước khi đưa vào RL
- các công cụ hiện có đang chuyển đổi dữ liệu theo cách nào

## Nội dung chính

- đọc và đối chiếu `LEF`, `DEF`, `SDC`, `SPEF`, netlist và các file liên quan
- làm rõ thông tin nào được giữ lại cho macroplacement
- phân tích cách `MacroPlacement` và `circuit_training` biểu diễn netlist, macro, port, pin, connectivity và placement
- mô tả luồng chuyển đổi từ dữ liệu thiết kế sang dữ liệu đầu vào của environment RL

## Đầu vào

- testcase có macro
- artifact EDA từ flow implementation
- tài liệu và công cụ chuyển đổi có sẵn

## Đầu ra

- sơ đồ chuyển đổi dữ liệu rõ ràng từ EDA sang RL
- hiểu được ý nghĩa của các file trung gian trong pipeline
- xác định được những khối dữ liệu cần thiết cho state, action, reward và placement cost

## Tiêu chí hoàn thành

- giải thích được luồng dữ liệu từ testcase đến dữ liệu dùng cho RL
- chỉ ra được công cụ hoặc bước nào sinh ra từng nhóm dữ liệu quan trọng
- xác định được pipeline có thể tái tạo hoặc mở rộng ở bước sau
