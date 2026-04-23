# Refine Placement Và Đánh Giá Lại Bằng EDA

## Mục tiêu

Tài liệu này tập trung vào việc đưa kết quả placement của giai đoạn trước quay trở lại flow EDA để refine và đánh giá lại bằng các chỉ số vật lý.

Ở giai đoạn này, trọng tâm là:

- đưa placement đã có vào lại quy trình physical design
- tiếp tục hoàn thiện các bước placement, CTS, route hoặc báo cáo khi cần
- đo lại các chỉ số implementation
- đối chiếu giữa proxy cost và kết quả vật lý thực tế

Mục tiêu cốt lõi là:

- khép kín quy trình thực dụng từ EDA sang placement rồi quay lại EDA
- xác nhận placement đầu ra có giá trị thực tế chứ không chỉ đúng ở mức proxy
- tạo baseline hoàn chỉnh để dùng cho báo cáo hoặc so sánh

## Vị Trí Trong Toàn Bộ Quy Trình

Sau khi đã có dữ liệu placement và kết quả đánh giá sơ bộ, giai đoạn này phải trả lời câu hỏi:

- placement đầu ra có thực sự cải thiện hoặc ít nhất hợp lệ khi đưa trở lại flow EDA hay không?

Đây là bước:

- nối ngược từ dữ liệu placement về implementation flow
- kiểm chứng chất lượng đầu ra bằng công cụ EDA thật
- chốt kết quả cuối cùng của quy trình triển khai thực dụng

## Bảng tổng hợp

| Hạng mục | Nội dung |
|---|---|
| Mục tiêu | Đưa placement đầu ra quay lại EDA để refine và đánh giá |
| Công việc | Chuyển placement về dữ liệu EDA phù hợp, chạy lại flow, trích xuất chỉ số, đối chiếu kết quả |
| Đầu vào | Placement từ giai đoạn trước, benchmark có macro, flow OpenROAD hoặc flow tương đương |
| Đầu ra | Kết quả implementation sau refine, báo cáo vật lý, số liệu đối chiếu với proxy cost |
| Tiêu chí hoàn thành | Placement được đưa trở lại EDA và có số liệu đánh giá rõ ràng |

## Đầu vào chính

- placement đầu ra từ bước placement hoặc RL
- benchmark có macro thật
- flow EDA đã dựng từ giai đoạn đầu
- các file công nghệ, netlist và constraint tương ứng

## Công cụ nên ưu tiên

`OpenROAD-flow-scripts`:

Là bộ script điều phối flow thiết kế số tự động.
Công dụng: tổ chức các bước chạy lại implementation để refine và lấy báo cáo.

`OpenROAD`:

Là công cụ physical design mã nguồn mở.
Công dụng: thực hiện placement, CTS, route, trích xuất và báo cáo lại kết quả implementation.

`plc_client` hoặc `PlacementCost`:

Là công cụ proxy cost của pipeline placement.
Công dụng: cung cấp số liệu để đối chiếu với kết quả vật lý sau khi refine.

## Hướng đi của giai đoạn

Giai đoạn này đi theo hướng thực dụng:

1. Lấy placement đầu ra từ bước trước.
2. Chuyển placement đó về dạng có thể dùng lại trong flow EDA.
3. Chạy lại flow implementation ở mức cần thiết.
4. Trích xuất báo cáo vật lý.
5. Đối chiếu các chỉ số vật lý với proxy cost đã có trước đó.

Điều quan trọng là:

- không cần tối ưu quá sâu ngay từ lần đầu
- cần ưu tiên kiểm tra tính hợp lệ và khả năng quay lại flow
- phải tạo được số liệu đủ rõ để kết luận

## Quy trình thực hiện

### Bước 1: Chuẩn bị placement đầu vào

Cần xác định rõ:

- placement nào được chọn để đánh giá lại
- placement đó đang ở dạng `.plc`, `.pb.txt`, hay dữ liệu trung gian khác
- có cần chuyển đổi sang DEF, TCL hoặc dạng placement mà flow EDA chấp nhận hay không

### Bước 2: Đưa placement quay lại flow EDA

Tùy flow đang dùng, có thể cần:

- sinh TCL đặt macro
- cập nhật DEF
- hoặc dùng công cụ chuyển đổi từ dữ liệu placement sang dữ liệu thiết kế vật lý

Mục tiêu của bước này là để flow EDA có thể đọc lại placement và tiếp tục chạy.

### Bước 3: Chạy lại implementation flow

Ở mức tối thiểu, nên chạy lại các bước cần thiết để:

- hợp thức hóa placement
- tiếp tục placement refinement
- chạy CTS và route nếu môi trường cho phép
- sinh báo cáo vật lý

### Bước 4: Trích xuất chỉ số vật lý

Cần lấy các chỉ số như:

- wirelength hoặc chiều dài dây
- density hoặc mức độ dồn cụm
- congestion nếu có
- timing hoặc slack nếu có
- tình trạng hợp lệ của placement

### Bước 5: Đối chiếu với proxy cost

Giai đoạn này cần so sánh:

- kết quả proxy ở bước placement trước đó
- kết quả implementation thực sau khi đưa về flow EDA

Mục tiêu của bước so sánh là:

- xem proxy có phản ánh đúng xu hướng chất lượng placement hay không
- xem placement đầu ra có thực sự hữu ích cho flow vật lý không

## Lệnh terminal cụ thể

Nếu bám theo flow OpenROAD đã dùng ở giai đoạn đầu, có thể chạy lại theo hướng:

```bash
cd /home/DATN/OpenROAD-flow-scripts/flow
env -u DISPLAY QT_QPA_PLATFORM=offscreen \
make DESIGN_CONFIG=./designs/nangate45/gcd/config.mk \
  YOSYS_EXE=/home/DATN/oss-cad-suite-20260421/bin/yosys \
  OPENROAD_EXE=/usr/bin/openroad \
  do-finish -j1
```

Nếu benchmark có macro và đã có cách đưa placement quay lại flow, phần này cần thay `DESIGN_CONFIG` và dữ liệu placement theo đúng testcase đang đánh giá.

Trong thực tế, giai đoạn này thường cần thêm một bước chuyển placement từ `.plc` hoặc dữ liệu trung gian sang dạng mà flow EDA có thể đọc trực tiếp.

## Đầu vào

- placement đầu ra từ bước placement hoặc RL
- benchmark thiết kế có macro
- flow OpenROAD hoặc flow implementation tương đương

## Đầu ra mong muốn

- placement đã được refine lại trong flow EDA
- báo cáo implementation sau refine
- số liệu đủ để so sánh với proxy cost
- kết luận thực dụng về chất lượng placement

## Tiêu chí hoàn thành

- placement đầu ra được đưa trở lại flow EDA thành công
- flow tiếp tục chạy được ở mức đánh giá mong muốn
- có số liệu vật lý để đối chiếu
- có kết luận rõ ràng về mức độ phù hợp của placement đầu ra

## Rủi ro và lưu ý

- placement từ pipeline RL không phải lúc nào cũng đưa ngược về EDA trực tiếp được
- có thể cần thêm bước chuyển đổi trung gian
- không nên kết luận chỉ dựa vào một chỉ số duy nhất
- nếu benchmark và flow chưa khớp hoàn toàn, nên ưu tiên chứng minh khả năng quay lại flow trước
