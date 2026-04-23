# Chuẩn Hóa Dữ Liệu Thiết Kế Cho Pipeline RL

## Mục tiêu

Tài liệu này tập trung vào việc dùng các công cụ có sẵn để chuyển dữ liệu EDA sang dữ liệu đầu vào chuẩn cho RL macroplacement.

Ở giai đoạn này không ưu tiên tự viết parser trước, mà ưu tiên:

- tận dụng `MacroPlacement` và `circuit_training`
- bám sát format mà hệ RL placement đang dùng
- tạo ra pipeline cơ bản từ dữ liệu physical design sang dữ liệu học tăng cường

Mục tiêu cốt lõi là:

- xác định rõ dữ liệu nào cần được lấy từ quy trình EDA
- chuẩn hóa dữ liệu đó theo luồng mà các công cụ RL placement hiện có có thể sử dụng
- tạo ra một pipeline cơ bản, có thể lặp lại, để phục vụ các bước học tăng cường tiếp theo

## Vị Trí Trong Toàn Bộ Quy Trình

Sau khi đã tạo được artifact EDA thật, giai đoạn này phải trả lời câu hỏi:

- làm sao dùng các artifact hoặc benchmark hiện có để tạo dữ liệu mà RL có thể đọc trực tiếp?

Ở đây, câu trả lời nên đi theo hướng:

- `LEF/DEF`
- translator có sẵn
- `netlist.pb.txt`
- `initial.plc` nếu có
- `plc_client` / `PlacementCost`

Nói theo ngôn ngữ chuyên môn hơn, đây là bước:

- chuyển từ dữ liệu thiết kế và placement vật lý sang dữ liệu mô tả bài toán RL
- tạo nền cho mô hình học tăng cường tiếp cận được thông tin về macro, kết nối, ràng buộc, và chi phí đánh giá placement

## Bảng tổng hợp

| Hạng mục | Nội dung |
|---|---|
| Mục tiêu | Dùng công cụ có sẵn để chuyển dữ liệu EDA sang dữ liệu chuẩn cho RL macroplacement |
| Công việc | Chọn benchmark có macro, dùng translator, sinh protobuf, kiểm tra `plc_client`, chốt đầu vào đầu ra |
| Đầu vào | `LEF`, `DEF`, benchmark có macro, công cụ từ `MacroPlacement` và `circuit_training` |
| Đầu ra | `netlist.pb.txt`, có thể kèm `initial.plc`, dữ liệu đọc được bởi `PlacementCost` / `plc_client` |
| Tiêu chí hoàn thành | Có một pipeline cơ bản từ EDA sang RL-format hoạt động được bằng công cụ có sẵn |

## Hướng triển khai

Giai đoạn này đi theo triết lý:

- dùng cái có sẵn trước
- chỉ viết thêm khi thật sự cần
- ưu tiên dựng được flow chuẩn của hệ `MacroPlacement + circuit_training`

Nói ngắn gọn:

- đây là cây cầu nối giữa EDA và RL

## Đầu vào thực tế

Đầu vào ở giai đoạn này không nên dừng ở `gcd`.

Lý do:

- `gcd` hữu ích để kiểm tra flow EDA
- nhưng không phù hợp cho RL macroplacement vì không có macro

Do đó, bước này phải chuyển sang benchmark có macro thật từ `MacroPlacement`.

Benchmark nên ưu tiên:

- `ariane133`
- `ariane136`
- `nvdla`
- `mempool`

## Nhóm dữ liệu đầu vào và vai trò của từng loại file

Ở giai đoạn này, dữ liệu đầu vào nên được nhìn theo từng nhóm chức năng thay vì chỉ như các định dạng rời rạc.

### 1. Dữ liệu hình học và placement

- `LEF`:
  - Là tệp mô tả thư viện vật lý.
  - Công dụng: cung cấp kích thước cell, macro, chân và thông tin lớp công nghệ.
- `DEF`:
  - Là tệp mô tả bố trí thiết kế.
  - Công dụng: cung cấp vị trí placement, boundary, component, net và port của thiết kế.

### 2. Dữ liệu ràng buộc thiết kế

- `SDC`:
  - Là tệp mô tả ràng buộc thời gian của thiết kế.
  - Công dụng: cung cấp thông tin clock và các ràng buộc logic-thời gian để giữ ngữ cảnh thiết kế.

### 3. Dữ liệu đánh giá hoặc tham chiếu sau route

- `SPEF`:
  - Là tệp mô tả parasitic sau route.
  - Công dụng: hỗ trợ các bước đánh giá sâu hơn như proxy timing hoặc phân tích sau implementation.

### 4. Dữ liệu benchmark có macro

- testcase có macro:
  - Là dữ liệu thiết kế phục vụ đúng bài toán macroplacement.
  - Công dụng: bảo đảm pipeline phản ánh đúng bản chất nghiên cứu thay vì chỉ chạy thử kỹ thuật.

## Mục tiêu

1. Chọn một benchmark có macro thật.
2. Chuẩn bị các dữ liệu EDA cần thiết của benchmark đó.
3. Dùng các công cụ chuyển đổi sẵn có trong `MacroPlacement`.
4. Kiểm tra dữ liệu sau chuyển đổi bằng công cụ đánh giá placement.
5. Xác nhận rằng dữ liệu tạo ra đã sẵn sàng để dùng trong RL loop ở bước tiếp theo.

Điểm quan trọng của hướng đi này là:

- không tự xây lại toàn bộ pipeline từ đầu
- ưu tiên đi theo chuẩn dữ liệu mà hệ sinh thái `MacroPlacement + circuit_training` đang sử dụng
- dùng giai đoạn này để ổn định đường truyền dữ liệu trước khi đi vào huấn luyện

## Công cụ có sẵn cần tận dụng

### 1. FormatTranslators

Đường dẫn:

- [MacroPlacement/CodeElements/FormatTranslators](/home/DATN/MacroPlacement/CodeElements/FormatTranslators)

- Là bộ công cụ chuyển đổi định dạng dữ liệu thiết kế.
- Công dụng: đưa dữ liệu EDA như `LEF/DEF` sang dạng mà pipeline RL placement có thể sử dụng.

### 2. CodeFlowIntegration

Đường dẫn:

- [MacroPlacement/CodeElements/CodeFlowIntegration/flow.py](/home/DATN/MacroPlacement/CodeElements/CodeFlowIntegration/flow.py)

- Là flow tích hợp nhiều khối xử lý dữ liệu thiết kế.
- Công dụng: kết nối các bước gridding, grouping, clustering và chuyển đổi dữ liệu thành một quy trình nhất quán.

### 3. Plc_client

Đường dẫn:

- [MacroPlacement/CodeElements/Plc_client](/home/DATN/MacroPlacement/CodeElements/Plc_client)

- Là công cụ mô phỏng và đánh giá placement theo kiểu circuit training.
- Công dụng: đọc dữ liệu placement và tính các chỉ số proxy như wirelength, density, congestion, adjacency và node mask.

### 4. Tài liệu format của circuit_training

Các tài liệu cần bám:

- [circuit_training/docs/NETLIST_FORMAT.md](/home/DATN/circuit_training/docs/NETLIST_FORMAT.md)
- [circuit_training/docs/PLACEMENT_COST.md](/home/DATN/circuit_training/docs/PLACEMENT_COST.md)

Đây là tài liệu chuẩn mô tả cách biểu diễn dữ liệu và cách đánh giá placement trong hệ circuit training.

## Quy trình thực hiện

### Bước 1: Chọn benchmark có macro thật

Không dùng `gcd` làm benchmark chính cho giai đoạn này.

Nên chọn một benchmark trong `MacroPlacement/Testcases` có macro.

Mục tiêu của bước này:

- có đầu vào đúng bản chất macroplacement
- không bị lệch bài toán RL

### Bước 2: Chuẩn bị dữ liệu đầu vào cho translator

Tùy theo benchmark và ví dụ có sẵn, đầu vào có thể là:

- `LEF/DEF`
- hoặc dữ liệu tương đương được flow tích hợp chấp nhận

Ở bước này cần xác định rõ:

- file nào là netlist
- file nào là placement
- file nào là thư viện công nghệ
- file nào giữ vai trò ràng buộc hoặc dữ liệu đánh giá bổ sung

### Bước 3: Dùng translator có sẵn để sinh protobuf

Mục tiêu:

- tạo ra dữ liệu mô tả netlist và placement theo chuẩn mà công cụ RL placement có thể đọc được

Đây là đầu ra kỹ thuật quan trọng nhất của giai đoạn này.

Nếu có ví dụ test sẵn trong `MacroPlacement`, nên bám đúng cách gọi đó trước.

## Lệnh terminal cụ thể

Trong repo hiện tại, cách chạy ổn định nhất cho giai đoạn này là dùng trực tiếp bộ dữ liệu mẫu Ariane đã có sẵn trong `MacroPlacement`, sau đó sinh `initial.plc` từ `netlist.pb.txt`.

Chạy:

```bash
cd /home/DATN/MacroPlacement/Flows/util
cp /home/DATN/MacroPlacement/CodeElements/FormatTranslators/test/LefDef2ProtocolBufferFormat/ariane.pb.txt ./netlist.pb.txt
python3 gen_plc_from_pb.py ./netlist.pb.txt
mv init.plc initial.plc
```

Đầu vào trực tiếp của lệnh trên:

- `ariane.pb.txt`

Đầu ra trực tiếp của lệnh trên:

- `netlist.pb.txt`
- `initial.plc`

Lưu ý thực tế:

- Ví dụ `LEF/DEF -> protobuf` trong `MacroPlacement` hiện phụ thuộc vào biến thể `OpenROAD` có lệnh `partition_design`.
- `OpenROAD` hệ thống trên máy này đọc được `LEF/DEF` nhưng dừng ở bước đó, nên baseline thực dụng nên dùng ngay `ariane.pb.txt` mẫu để bảo đảm pipeline chạy được.

### Bước 4: Kiểm tra tính hợp lệ của dữ liệu protobuf

Sau khi có `netlist.pb.txt`, cần kiểm tra:

- có đọc được bằng công cụ của `circuit_training` hoặc `plc_client` không
- node type có hợp lý không
- macro, port, pin, adjacency có được biểu diễn đúng không

### Bước 5: Nạp hoặc tạo `initial.plc`

Nếu pipeline hoặc benchmark có placement khởi tạo:

- dùng luôn `initial.plc`

Nếu chưa có:

- giai đoạn này có thể tạm dừng ở `netlist.pb.txt`
- hoặc tạo placement khởi tạo ở bước sau nếu công cụ hỗ trợ

### Bước 6: Kiểm tra với `PlacementCost` / `plc_client`

Giai đoạn này nên chứng minh được:

- protobuf sinh ra có thể được dùng để tính proxy cost
- có thể lấy:
  - wirelength cost
  - density cost
- congestion cost
- adjacency
- node mask

## Đầu vào

- benchmark có macro
- `LEF`
- `DEF`
- công cụ translator trong `MacroPlacement`
- `circuit_training`

## Đầu ra mong muốn

Đầu ra nên được mô tả theo giá trị sử dụng thay vì chỉ theo tên file:

- dữ liệu có thể biểu diễn được netlist, macro, port, connectivity và placement theo chuẩn mà công cụ RL placement có thể đọc
- nếu có placement khởi tạo, dữ liệu đó phải có khả năng khôi phục hoặc nạp lại placement ban đầu
- dữ liệu sinh ra phải đủ để công cụ proxy cost thực hiện đánh giá placement

Ở mức hiện thực kỹ thuật, điều này thường tương ứng với:

- dữ liệu netlist ở chuẩn protobuf
- dữ liệu placement khởi tạo như `.plc` nếu có

Đầu ra kiểm chứng:

- dữ liệu đọc được bởi `plc_client`
- cost proxy tính được thành công

## Tiêu chí hoàn thành

- đã chọn được benchmark có macro thật
- đã dùng công cụ có sẵn để chuyển sang protobuf
- có `netlist.pb.txt`
- dữ liệu đó đọc được bằng hệ công cụ đánh giá proxy cost
- nếu có thêm `initial.plc` thì càng hoàn chỉnh

## Rủi ro và lưu ý

- không nên cố ép `gcd` thành benchmark macroplacement
- không nên tự viết parser thay cho translator ở giai đoạn này, phần đó sẽ mở rộng ở nhánh nghiên cứu sâu hơn
- nếu translator yêu cầu flow hoặc dependency cụ thể, nên theo đúng ví dụ có sẵn trước
