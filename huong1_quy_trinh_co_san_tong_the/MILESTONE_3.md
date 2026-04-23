# Chạy Baseline Placement Hoặc Học Tăng Cường

## Mục tiêu

Tài liệu này tập trung vào việc đưa dữ liệu đã chuẩn hóa ở giai đoạn trước vào một vòng lặp placement hoặc học tăng cường có thể chạy được, quan sát được và cho ra kết quả rõ ràng.

Đây là bước mà quy trình bắt đầu đi vào phần thực thi của bài toán macroplacement:

- nạp dữ liệu thiết kế vào environment phù hợp
- dùng placement cost hoặc proxy cost để đánh giá kết quả
- chạy baseline placement hoặc huấn luyện ngắn
- lưu placement đầu ra để hiển thị, phân tích và dùng tiếp ở bước refine kế tiếp

## Bảng tổng hợp

| Hạng mục | Nội dung |
|---|---|
| Mục tiêu | Chạy được baseline placement hoặc RL loop trên benchmark có macro |
| Công việc | Nạp dữ liệu, kết nối environment, cấu hình reward, chạy baseline, lưu kết quả |
| Đầu vào | Dữ liệu từ giai đoạn trước, benchmark có macro, công cụ placement cost hoặc environment có sẵn |
| Đầu ra | Placement đầu ra, log chạy, reward history, cost proxy |
| Tiêu chí hoàn thành | Có một quy trình placement hoặc RL chạy được và sinh ra kết quả có thể đánh giá |

## Đầu vào chính

- dữ liệu thiết kế đã được chuẩn hóa từ giai đoạn trước
- benchmark có macro thật
- `plc_client` hoặc công cụ đánh giá placement tương đương
- environment hoặc pipeline RL có sẵn trong `MacroPlacement` hay `circuit_training`

## Công cụ nên ưu tiên

`plc_client`:

Là công cụ đánh giá placement theo kiểu `circuit_training`.
Công dụng: đọc dữ liệu placement, tính proxy cost và cung cấp thông tin để xây reward.

`PlacementCost`:

Là cơ chế đánh giá nhanh chất lượng placement.
Công dụng: lượng hóa wirelength, density, congestion và các tín hiệu chất lượng placement.

environment RL:

Là môi trường tương tác giữa agent và bài toán placement.
Công dụng: nhận action, cập nhật trạng thái placement và trả về reward.

## Hướng đi của giai đoạn

Giai đoạn này đi theo hướng thực dụng:

1. Nạp dữ liệu đã tạo được ở giai đoạn trước.
2. Kiểm tra dữ liệu có đọc được bởi công cụ placement cost hay environment không.
3. Dùng proxy cost để xây reward hoặc tiêu chí đánh giá.
4. Chạy một baseline rõ ràng.
5. Lưu kết quả placement, reward và log để đối chiếu.

Baseline ở giai đoạn đầu không cần quá phức tạp. Điều quan trọng là pipeline phải:

- chạy được ổn định
- sinh ra placement đầu ra
- cho phép quan sát và so sánh kết quả

## Quy trình thực hiện

### Bước 1: Chuẩn bị dữ liệu đầu vào

Sử dụng dữ liệu đã qua bước chuyển đổi ở giai đoạn trước.

Ở bước này cần xác nhận:

- benchmark có macro thật
- dữ liệu đọc được ổn định
- placement ban đầu hoặc cấu hình canvas có thể nạp lại

### Bước 2: Kết nối vào environment

Mục tiêu của bước này là tạo được một vòng lặp placement có thể nhận action và trả về reward hoặc cost.

Ở đây nên ưu tiên:

- tận dụng environment có sẵn nếu có
- tránh tự viết lại toàn bộ logic khi chưa cần thiết

### Bước 3: Cấu hình reward hoặc cost đánh giá

Reward nên bám vào các chỉ số đã có sẵn trong công cụ hiện có:

- wirelength
- density
- congestion

Nếu cần có thể bổ sung overlap penalty hoặc out-of-bounds penalty, nhưng trọng tâm vẫn là giữ baseline đơn giản và dễ kiểm chứng.

### Bước 4: Chạy baseline

Baseline có thể là:

- một vòng huấn luyện ngắn
- một heuristic placement rõ ràng
- hoặc một policy đơn giản để kiểm tra pipeline

Trong repo hiện tại, baseline thực dụng nhất đang được triển khai là:

- nạp `netlist.pb.txt` và `initial.plc`
- đánh giá placement hiện tại
- xuất số liệu proxy
- xuất hình placement để kiểm tra trực quan

Đây là bước chạy thực tế đầu tiên trước khi thay bằng environment RL hoàn chỉnh.

Mục tiêu của bước này là xác nhận:

- pipeline dữ liệu hoạt động đúng
- reward thay đổi hợp lý
- placement đầu ra có thể lưu và xem lại

### Bước 5: Lưu và hiển thị kết quả

Cần ghi lại:

- placement đầu ra
- reward theo bước hoặc theo episode
- cost proxy tương ứng
- benchmark và điều kiện chạy

Kết quả nên có thể quan sát lại bằng:

- báo cáo số liệu
- file placement
- GUI hoặc công cụ hiển thị phù hợp nếu cần

## Lệnh terminal cụ thể

Trước hết chuẩn bị dữ liệu:

```bash
cd /home/DATN/MacroPlacement/Flows/util
cp /home/DATN/MacroPlacement/CodeElements/FormatTranslators/test/LefDef2ProtocolBufferFormat/ariane.pb.txt ./netlist.pb.txt
python3 gen_plc_from_pb.py ./netlist.pb.txt
mv init.plc initial.plc
```

Sau đó có thể kiểm tra và xem placement bằng công cụ có sẵn:

```bash
cd /home/DATN/MacroPlacement/CodeElements/VisualPlacement
python3 visual_placement.py \
  --netlist /home/DATN/MacroPlacement/Flows/util/netlist.pb.txt \
  --plc /home/DATN/MacroPlacement/Flows/util/initial.plc
```

Nếu muốn thử đọc dữ liệu bằng công cụ proxy cost của `circuit_training`:

```bash
cd /home/DATN
python3 circuit_training/circuit_training/environment/plc_client_main.py \
  --netlist_file /home/DATN/MacroPlacement/Flows/util/netlist.pb.txt
```

Đầu vào trực tiếp:

- `netlist.pb.txt`
- `initial.plc`

Đầu ra cần quan sát:

- placement trên cửa sổ hiển thị
- các chỉ số proxy cost nếu môi trường `circuit_training` đã đủ dependency

Xem kết quả:

- nếu đang dùng VNC thì mở trực tiếp cửa sổ hiển thị
- nếu đang dùng VS Code từ xa thì có thể dùng môi trường desktop hoặc X11/VNC để xem

## Đầu ra mong muốn

- một baseline placement hoặc RL loop có thể chạy được
- placement đầu ra để làm đầu vào cho giai đoạn refine và đánh giá tiếp theo
- log và cost proxy để phân tích
- kết quả đủ rõ để trình bày hoặc demo

## Tiêu chí hoàn thành

- pipeline placement hoặc RL chạy được trên benchmark đã chọn
- cost hoặc reward được tính ổn định
- placement đầu ra được lưu lại thành công
- có dữ liệu đánh giá để so sánh giữa các lần chạy
