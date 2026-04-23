# State, Action, Reward Và Environment

## Mục tiêu

Tài liệu này tập trung vào việc xây dựng và kiểm soát sâu phần tương tác giữa dữ liệu thiết kế và môi trường học tăng cường.

Giai đoạn này làm rõ:

- state được xây từ thông tin nào
- action tác động lên placement như thế nào
- reward được hình thành từ các chỉ số vật lý nào
- placement cost và environment phản ánh bài toán thực ra sao

## Nội dung chính

- mô tả cách tạo state từ netlist, macro, vị trí, canvas và connectivity
- xác định không gian action cho macroplacement
- xây reward từ wirelength, density, congestion, overlap và các ràng buộc khác
- phân tích cách baseline heuristic hoặc policy RL tương tác với environment

## Đầu vào

- dữ liệu đã được chuẩn hóa ở giai đoạn trước
- benchmark có macro
- công cụ hoặc mô hình RL được chọn

## Đầu ra

- mô tả rõ environment RL của bài toán
- baseline tối ưu có thể giải thích được
- cơ sở để so sánh giữa pipeline dùng sẵn và pipeline nghiên cứu sâu

## Tiêu chí hoàn thành

- giải thích được cấu trúc state, action và reward
- chạy được một vòng lặp placement hoặc RL có thể quan sát
- liên hệ được kết quả đầu ra với chất lượng placement thực tế
