# Tài Liệu Tổng Hợp Dự Án DATN

## Mục lục

1. Giới thiệu dự án
2. Bài toán trung tâm: macro placement trong thiết kế vi mạch
3. Cơ sở về thiết kế vi mạch số và VLSI
4. Tổng quan EDA và physical design flow
5. Vì sao học tăng cường phù hợp với macro placement
6. Các khái niệm RL đang dùng trong dự án
7. AlphaChip, Circuit Training và hướng tiếp cận của DATN
8. Kiến trúc tổng thể của repo
9. Các thành phần kỹ thuật chính trong `MacroPlacement`
10. `rl_macroplacement_agent`: phần RL mà dự án tự xây
11. Pipeline end-to-end của DATN
12. Proxy cost, reward và các metric đánh giá
13. Các định dạng file trong dự án và ý nghĩa của chúng
14. Giải thích trực tiếp hai format quan trọng nhất: `.pb.txt` và `.plc`
15. Công cụ open-source thay thế Genus, Innovus và các tool thương mại
16. Hướng dẫn sử dụng stack open-source trong đồ án
17. DREAMPlace trong dự án này đóng vai trò gì
18. Milestone và trạng thái hiện tại của DATN
19. Khuyến nghị nghiên cứu và mở rộng
20. Kết luận

---

## Chương 1. Giới thiệu dự án

`DATN-1` là dự án nghiên cứu ứng dụng **học tăng cường** cho bài toán **macro placement** trong **thiết kế vi mạch số**. Hướng nghiên cứu bám theo tinh thần của **AlphaChip / Circuit Training**, nhưng được triển khai bằng một hệ công cụ **open-source**, có thể build, chạy lại và kiểm chứng trong môi trường thực tế.

Ý tưởng lõi của dự án là:

```text
benchmark có macro thật
    -> chuyển sang dữ liệu kiểu Circuit Training
    -> dùng RL học chính sách đặt macro
    -> sinh placement .plc
    -> đưa placement quay lại flow vật lý
    -> đánh giá bằng proxy cost và QoR vật lý
```

Repo này không cố tái tạo nguyên xi hệ thống nội bộ của Google. Thay vào đó, nó xây một **pipeline nghiên cứu thực dụng**, minh bạch và có khả năng tái lập.

### 1.1 Bối cảnh của đề tài

Trong thiết kế vi mạch hiện đại, chi phí phát triển ngày càng tăng do:

- độ phức tạp của thiết kế tăng mạnh
- số lượng macro và standard cell rất lớn
- các ràng buộc timing, power và routing ngày càng chặt
- chu kỳ tối ưu vật lý chiếm thời gian đáng kể trong toàn bộ flow

Trong bối cảnh đó, các phương pháp tối ưu truyền thống vẫn giữ vai trò chủ đạo, nhưng học máy và đặc biệt là học tăng cường đã mở ra một hướng tiếp cận mới: thay vì chỉ giải một bài toán tối ưu đơn lẻ, hệ thống có thể học một **chính sách ra quyết định tuần tự** để tái sử dụng trên nhiều episode hoặc nhiều thiết kế tương tự.

### 1.2 Mục đích của đồ án

Mục đích tổng quát của đồ án là xây dựng một pipeline nghiên cứu hoàn chỉnh cho bài toán macro placement bằng học tăng cường, dựa trên các công cụ open-source, nhằm:

- hiểu đúng bản chất của bài toán macro placement trong physical design
- tái hiện được một flow gần với Circuit Training ở mức nghiên cứu
- kiểm chứng khả năng áp dụng RL vào thiết kế vi mạch
- tạo nền tảng để so sánh công bằng giữa RL và các baseline placement truyền thống

### 1.3 Mục tiêu tổng quát

Mục tiêu tổng quát của đồ án là:

> Xây dựng, phân tích và đánh giá một hệ thống macro placement dựa trên học tăng cường, có khả năng hoạt động end-to-end trên stack open-source và có thể kết nối trở lại flow physical design để kiểm chứng chất lượng placement.

### 1.4 Mục tiêu cụ thể

Các mục tiêu cụ thể bao gồm:

1. Nghiên cứu cơ sở lý thuyết về VLSI, EDA, physical design và macro placement.
2. Nghiên cứu cơ sở toán học của học tăng cường, đặc biệt là MDP, policy gradient, actor-critic và PPO.
3. Khảo sát và tích hợp các thành phần của `MacroPlacement`, `OpenROAD`, `ORFS`, `DREAMPlace` và `rl_macroplacement_agent`.
4. Chuẩn hóa dữ liệu đầu vào cho RL dưới dạng `netlist.pb.txt` và `.plc`.
5. Xây dựng và đánh giá baseline RL bằng `MaskablePPO`.
6. Phát triển hướng agent graph-based gần tinh thần AlphaChip hơn.
7. Chuyển placement đầu ra của RL về backend vật lý để đánh giá QoR.
8. Xây dựng bộ tài liệu học thuật, kỹ thuật và thực nghiệm phục vụ báo cáo tốt nghiệp.

### 1.5 Câu hỏi nghiên cứu

Đồ án này xoay quanh các câu hỏi nghiên cứu chính sau:

1. Bài toán macro placement có thể được mô hình hóa hiệu quả như một bài toán học tăng cường hay không?
2. Biểu diễn trạng thái nào là phù hợp hơn cho macro placement: vector đặc trưng đơn giản hay biểu diễn đồ thị netlist?
3. Reward dựa trên proxy cost có đủ hữu ích để dẫn dắt policy học placement chất lượng hay không?
4. Một stack open-source có thể thay thế đến mức nào cho pipeline dùng tool thương mại trong nghiên cứu macro placement?
5. Kết quả placement sinh bởi RL có thể được đưa trở lại OpenROAD để đánh giá vật lý thực tế hay không?

### 1.6 Đối tượng và phạm vi nghiên cứu

#### Đối tượng nghiên cứu

Đối tượng nghiên cứu của đồ án là:

- bài toán macro placement trong physical design
- các phương pháp học tăng cường cho ra quyết định tuần tự
- hệ công cụ open-source phục vụ physical design và placement research

#### Phạm vi nghiên cứu

Đồ án tập trung vào:

- macro placement cho thiết kế số có macro thật
- benchmark từ `MacroPlacement`
- stack open-source gồm `Yosys`, `OpenROAD`, `ORFS`, `DREAMPlace`, `Gymnasium`, `Stable-Baselines3`

Đồ án không đặt mục tiêu:

- tái tạo đầy đủ hệ thống production của Google AlphaChip
- thay thế hoàn toàn flow signoff thương mại trong công nghiệp
- chứng minh tính tối ưu tuyệt đối của RL trên mọi benchmark

### 1.7 Phương pháp nghiên cứu

Đồ án sử dụng kết hợp các phương pháp:

- **nghiên cứu lý thuyết**: đọc tài liệu về RL, VLSI, EDA, macro placement và Circuit Training
- **nghiên cứu hệ thống**: phân tích cấu trúc repo, benchmark, format và flow
- **thực nghiệm tính toán**: huấn luyện agent RL, chạy baseline physical design, chấm placement
- **so sánh đánh giá**: đối chiếu RL với placement ban đầu, placement đã legalized và DREAMPlace
- **phân tích kỹ thuật**: đánh giá tính khả thi của việc nối RL với backend vật lý

### 1.8 Ý nghĩa khoa học và thực tiễn

#### Ý nghĩa khoa học

- Hệ thống hóa tri thức giao thoa giữa RL và EDA.
- Làm rõ cách mô hình hóa bài toán macro placement dưới dạng MDP.
- Phân tích vai trò của proxy cost trong huấn luyện RL cho chip design.

#### Ý nghĩa thực tiễn

- Tạo pipeline open-source có thể chạy lại được cho nghiên cứu.
- Giảm phụ thuộc vào tool thương mại trong giai đoạn nghiên cứu học thuật.
- Tạo nền tảng cho các khóa luận, luận văn hoặc bài báo tiếp theo.

### 1.9 Đóng góp dự kiến của đồ án

Các đóng góp chính của đồ án có thể trình bày như sau:

- Xây dựng tài liệu hệ thống về RL cho macro placement trong ngữ cảnh open-source.
- Tích hợp được pipeline từ dữ liệu `MacroPlacement` tới huấn luyện RL và quay lại OpenROAD.
- Xây dựng baseline `MaskablePPO` và nhánh AlphaChip-like graph-based.
- Chuẩn hóa và giải thích rõ vai trò của các định dạng như `netlist.pb.txt`, `.plc`, `.def`, `.lef`, `.odb`, `.sdc`, `.spef`.
- Thiết lập nền tảng so sánh giữa RL và các baseline placement truyền thống như DREAMPlace.

### 1.10 Cấu trúc của tài liệu

Tài liệu này được tổ chức theo hướng từ nền tảng lý thuyết tới hệ thống thực thi:

- các chương đầu trình bày bối cảnh, mục tiêu và cơ sở VLSI/EDA
- các chương giữa tập trung vào học tăng cường, Circuit Training và kiến trúc repo
- các chương sau trình bày flow thực nghiệm, format dữ liệu, công cụ thay thế và lộ trình phát triển
- phần phụ lục tóm tắt nhanh những format và tool quan trọng nhất

---

## Chương 2. Bài toán trung tâm: macro placement trong thiết kế vi mạch

Trong physical design, `macro` là các khối cứng có kích thước lớn, ví dụ:

- SRAM
- register file
- memory compiler block
- accelerator block
- IP block lớn

Macro placement là bài toán quyết định:

- đặt từng macro ở đâu trên chip
- có quay hoặc flip macro hay không
- quan hệ hình học giữa các macro
- khoảng cách giữa macro với IO, cụm logic, nguồn clock

Một placement tốt giúp:

- giảm wirelength
- giảm nghẽn routing
- cải thiện timing
- tăng khả năng route thành công
- giảm rủi ro phải sửa flow ở các bước sau

Macro placement khó vì:

- không gian tìm kiếm rất lớn
- quyết định mang tính tuần tự
- các quyết định đầu làm thay đổi mạnh các quyết định sau
- đánh giá placement tương đối đắt
- có nhiều ràng buộc hình học và vật lý

Đây là lý do bài toán này rất phù hợp với các kỹ thuật tối ưu hóa tuần tự như RL.

---

## Chương 3. Cơ sở về thiết kế vi mạch số và VLSI

### 3.1 VLSI là gì

**VLSI** là viết tắt của `Very Large Scale Integration`, tức là tích hợp số lượng rất lớn transistor lên một vi mạch. Trong ngữ cảnh đồ án này, VLSI chủ yếu nói đến:

- thiết kế mạch số
- synthesis từ RTL xuống gate-level
- floorplan, placement, CTS, routing
- đánh giá timing, power, congestion, area

### 3.2 Các tầng biểu diễn thiết kế

Một thiết kế số thường được mô tả qua các tầng:

1. Mức hành vi và RTL
2. Gate-level netlist
3. Thư viện công nghệ và thông tin hình học
4. Floorplan vật lý
5. Placement
6. Routing
7. Signoff và report

### 3.3 Một số khái niệm cần nắm

- `RTL`: mô tả logic bằng Verilog/SystemVerilog
- `Standard cell`: cell logic chuẩn từ thư viện
- `Macro`: block lớn, cứng, có hình học cố định
- `Netlist`: đồ thị kết nối logic
- `Pin/Port`: chân kết nối
- `Floorplan`: định nghĩa die/core, row, vùng macro, vùng cấm
- `Placement`: đặt vị trí phần tử
- `CTS`: clock tree synthesis
- `Routing`: nối dây vật lý
- `QoR`: quality of results, gồm timing, power, area, wirelength, congestion, routeability

---

## Chương 4. Tổng quan EDA và physical design flow

Flow vật lý chuẩn thường có dạng:

```text
RTL -> Synthesis -> Floorplan -> Placement -> CTS -> Routing -> Signoff
```

### 4.1 RTL

Đầu vào là các file `.v`, `.sv`. Đây là mô tả logic của thiết kế.

### 4.2 Synthesis

Synthesis biến RTL thành gate-level netlist dựa trên thư viện `.lib`. Trong đồ án, vai trò này được thay bởi `Yosys`.

### 4.3 Floorplan

Bước này xác định:

- kích thước die/core
- row placement
- vị trí IO
- ràng buộc macro và blockage
- mạng nguồn cơ bản

### 4.4 Placement

Gồm:

- macro placement
- standard-cell placement
- legalize, refine

### 4.5 CTS

Clock tree synthesis thêm và chỉnh mạng clock để cân bằng skew, latency, timing.

### 4.6 Routing

Bao gồm:

- global routing
- detailed routing
- tạo guide và dây thật

### 4.7 Signoff và report

Đánh giá:

- WNS
- TNS
- routed wirelength
- congestion
- power
- parasitics

Trong repo hiện tại, OpenROAD và ORFS là backend vật lý open-source chính để thực hiện các bước trên.

---

## Chương 5. Vì sao học tăng cường phù hợp với macro placement

Macro placement có bản chất quyết định tuần tự:

```text
quan sát trạng thái hiện tại
    -> chọn vị trí cho macro hiện tại
    -> cập nhật layout tạm thời
    -> nhận phản hồi chất lượng
    -> tiếp tục cho macro kế tiếp
```

Điều này rất gần với mô hình **Markov Decision Process** trong RL.

Ưu điểm của RL trong ngữ cảnh này:

- học được policy thay vì chỉ tối ưu một nghiệm đơn lẻ
- có thể tái dùng trên nhiều episode
- phù hợp với action masking khi không phải mọi vị trí đều hợp lệ
- có thể kết hợp thông tin đồ thị netlist và trạng thái placement

Khó khăn của RL:

- reward có thể thưa
- chi phí train cao
- dễ lệ thuộc thiết kế cụ thể
- cần môi trường chấm điểm ổn định
- cần cách biểu diễn trạng thái tốt

DATN xử lý điều đó bằng cách dùng:

- `PlacementCost / plc_client_os` làm evaluator
- `MaskablePPO` cho baseline
- agent graph-based AlphaChip-like cho hướng nghiên cứu chính

---

## Chương 6. Các khái niệm RL đang dùng trong dự án

### 6.1 MDP

Một bài toán RL được mô hình hóa bởi:

$$
\mathcal{M} = (\mathcal{S}, \mathcal{A}, P, R, \gamma)
$$

Trong đó:

- $\mathcal{S}$ là tập trạng thái
- $\mathcal{A}$ là tập hành động
- $P(s' \mid s,a)$ là xác suất chuyển trạng thái
- $R(s,a)$ hoặc $R(s,a,s')$ là hàm thưởng
- $\gamma \in [0,1)$ là hệ số chiết khấu

Trong macro placement:

- `State`: thông tin netlist, macro hiện tại, grid, placement state, mask
- `Action`: chọn grid cell hoặc vị trí hợp lệ cho macro hiện tại
- `Reward`: cải thiện chi phí placement hoặc terminal reward
- `Episode`: đặt xong một chuỗi macro
- `Policy`: chiến lược đặt macro

### 6.2 Return và discounted return

Tổng phần thưởng tích lũy kể từ thời điểm $t$ được gọi là **return**:

$$
G_t = \sum_{k=0}^{\infty} \gamma^k r_{t+k+1}
$$

Nếu episode hữu hạn, có thể viết:

$$
G_t = r_{t+1} + \gamma r_{t+2} + \gamma^2 r_{t+3} + \cdots + \gamma^{T-t-1}r_T
$$

Ý nghĩa của $\gamma$:

- nếu $\gamma$ nhỏ, agent ưu tiên lợi ích ngắn hạn
- nếu $\gamma$ lớn, agent quan tâm nhiều hơn đến chất lượng placement cuối cùng

Trong macro placement, điều này đặc biệt quan trọng vì một quyết định đầu episode có thể ảnh hưởng mạnh tới tổng chi phí khi placement hoàn tất.

### 6.3 Policy

Policy mô tả xác suất chọn hành động tại một trạng thái:

$$
\pi(a \mid s) = \Pr(A_t = a \mid S_t = s)
$$

Nếu policy được tham số hóa bởi mạng nơ-ron với tham số $\theta$:

$$
\pi_\theta(a \mid s)
$$

Trong bài toán của đồ án:

- đầu vào policy là trạng thái placement hiện tại
- đầu ra policy là phân phối xác suất trên các grid cell hợp lệ

### 6.4 Value function

**State-value function**:

$$
V^\pi(s) = \mathbb{E}_\pi[G_t \mid S_t = s]
$$

**Action-value function**:

$$
Q^\pi(s,a) = \mathbb{E}_\pi[G_t \mid S_t = s, A_t = a]
$$

Ý nghĩa:

- $V^\pi(s)$ cho biết trạng thái $s$ tốt đến mức nào nếu tiếp tục làm theo policy $\pi$
- $Q^\pi(s,a)$ cho biết hành động $a$ tại trạng thái $s$ tốt đến mức nào

### 6.5 Advantage function

Advantage đo mức tốt hơn hay kém hơn của một hành động so với kỳ vọng trung bình tại trạng thái:

$$
A^\pi(s,a) = Q^\pi(s,a) - V^\pi(s)
$$

Nếu $A^\pi(s,a) > 0$, hành động đó tốt hơn mức trung bình của trạng thái. Nếu âm, hành động đó kém hơn.

Trong PPO và actor-critic, advantage là đại lượng rất quan trọng vì nó làm giảm phương sai so với việc dùng trực tiếp return.

### 6.6 Bellman expectation equation

Phương trình Bellman cho state-value:

$$
V^\pi(s) =
\sum_a \pi(a \mid s)\sum_{s',r} P(s',r \mid s,a)
\left[r + \gamma V^\pi(s')\right]
$$

Phương trình Bellman cho action-value:

$$
Q^\pi(s,a) =
\sum_{s',r} P(s',r \mid s,a)
\left[
r + \gamma \sum_{a'} \pi(a' \mid s')Q^\pi(s',a')
\right]
$$

Bellman equation cho thấy giá trị hiện tại bằng:

- phần thưởng tức thời
- cộng với giá trị tương lai đã chiết khấu

### 6.7 Bellman optimality equation

Giá trị tối ưu trạng thái:

$$
V^*(s) =
\max_a \sum_{s',r} P(s',r \mid s,a)
\left[r + \gamma V^*(s')\right]
$$

Giá trị tối ưu hành động:

$$
Q^*(s,a) =
\sum_{s',r} P(s',r \mid s,a)
\left[r + \gamma \max_{a'} Q^*(s',a')\right]
$$

Trong placement, tối ưu toàn cục rất khó tìm trực tiếp vì không gian hành động rất lớn, do đó policy gradient và PPO trở thành lựa chọn thực tế hơn so với việc giải Bellman optimality một cách chính xác.

### 6.8 Action masking

Không phải mọi ô lưới đều hợp lệ cho macro hiện tại. Vì vậy dự án dùng `MaskablePPO` để:

- chặn vị trí gây overlap
- chặn vị trí ra ngoài canvas
- chỉ cho agent chọn hành động hợp lệ

Về mặt hình thức, ta có thể xem mask như một hàm:

$$
m(s,a) \in \{0,1\}
$$

trong đó:

- $m(s,a)=1$ nghĩa là hành động hợp lệ
- $m(s,a)=0$ nghĩa là hành động bị cấm

Phân phối policy hiệu dụng chỉ còn trên tập hành động hợp lệ:

$$
\mathcal{A}_{\mathrm{valid}}(s) = \{a \in \mathcal{A} \mid m(s,a)=1\}
$$

### 6.9 Reward

Repo hiện có hai kiểu reward chính:

- **stepwise reward**:

$$
r_t = \alpha \left(C_{t-1} - C_t\right)
$$

- **terminal reward**:

$$
R = \alpha \left(C_{\mathrm{init}} - C_{\mathrm{final}}\right)
$$

Trong đó `C` là proxy cost.

Thiết kế reward là vấn đề rất quan trọng:

- reward quá thưa làm train khó
- reward quá cục bộ có thể khiến agent tối ưu ngắn hạn
- reward không đồng bộ với QoR thật sẽ gây sai lệch mục tiêu nghiên cứu

### 6.10 Temporal-Difference error

Sai số TD cơ bản:

$$
\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)
$$

Trong actor-critic:

$$
\delta_t = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)
$$

TD error cho biết critic đang đánh giá thiếu hay thừa giá trị trạng thái hiện tại.

### 6.11 Policy gradient

Mục tiêu tối ưu policy:

$$
J(\theta) = \mathbb{E}_{\pi_\theta}[G_t]
$$

Định lý policy gradient:

$$
\nabla_\theta J(\theta)
=
\mathbb{E}_{\pi_\theta}
\left[
\nabla_\theta \log \pi_\theta(a_t \mid s_t)\, Q^{\pi_\theta}(s_t,a_t)
\right]
$$

Khi dùng advantage:

$$
\nabla_\theta J(\theta)
=
\mathbb{E}_{\pi_\theta}
\left[
\nabla_\theta \log \pi_\theta(a_t \mid s_t)\, A^{\pi_\theta}(s_t,a_t)
\right]
$$

Ý nghĩa trực giác:

- tăng xác suất cho hành động tốt
- giảm xác suất cho hành động xấu

### 6.12 REINFORCE và baseline

Loss của REINFORCE:

$$
\mathcal{L}_{\mathrm{policy}}
=
-\mathbb{E}\left[\log \pi_\theta(a_t \mid s_t)\, G_t\right]
$$

Nếu dùng baseline $b(s_t)$:

$$
\mathcal{L}_{\mathrm{policy}}
=
-\mathbb{E}\left[\log \pi_\theta(a_t \mid s_t)\, (G_t - b(s_t))\right]
$$

Baseline giúp giảm phương sai mà không làm sai lệch gradient kỳ vọng.

### 6.13 Actor-Critic

Trong actor-critic:

- **actor** học policy
- **critic** ước lượng value function

Loss actor:

$$
\mathcal{L}_{\mathrm{actor}}
=
-\mathbb{E}\left[\log \pi_\theta(a_t \mid s_t)\, A_t\right]
$$

Loss critic:

$$
\mathcal{L}_{\mathrm{critic}}
=
\mathbb{E}\left[(V_\phi(s_t)-\hat{V}_t)^2\right]
$$

Entropy của policy:

$$
\mathcal{H}(\pi_\theta(\cdot \mid s))
=
-\sum_a \pi_\theta(a \mid s)\log \pi_\theta(a \mid s)
$$

Loss tổng:

$$
\mathcal{L}
=
\mathcal{L}_{\mathrm{actor}}
+
c_v \mathcal{L}_{\mathrm{critic}}
-
c_e \mathcal{H}
$$

Entropy bonus giữ cho policy còn khả năng khám phá, tránh sụp sớm vào nghiệm cục bộ.

### 6.14 Generalized Advantage Estimation

GAE dùng để ước lượng advantage ổn định hơn:

$$
A_t^{\mathrm{GAE}(\gamma,\lambda)}
=
\sum_{l=0}^{\infty}(\gamma \lambda)^l \delta_{t+l}
$$

hay viết tường minh:

$$
A_t
=
\delta_t + \gamma\lambda \delta_{t+1}
+ (\gamma\lambda)^2 \delta_{t+2} + \cdots
$$

Vai trò của $\lambda$:

- $\lambda$ nhỏ: bias cao hơn nhưng variance thấp hơn
- $\lambda$ lớn: gần Monte Carlo hơn, variance cao hơn

### 6.15 PPO

PPO là thuật toán policy gradient ổn định, phù hợp khi:

- action space rời rạc
- cần cập nhật policy dần dần
- muốn huấn luyện actor-critic

Tỉ số giữa policy mới và policy cũ:

$$
\rho_t(\theta)
=
\frac{\pi_\theta(a_t \mid s_t)}
{\pi_{\theta_{\mathrm{old}}}(a_t \mid s_t)}
$$

Hàm mục tiêu clipped PPO:

$$
\mathcal{L}^{\mathrm{CLIP}}(\theta)
=
\mathbb{E}_t
\left[
\min
\left(
\rho_t(\theta)A_t,\;
\operatorname{clip}(\rho_t(\theta),1-\epsilon,1+\epsilon)A_t
\right)
\right]
$$

Nếu viết dưới dạng loss cần tối thiểu hóa:

$$
\mathcal{L}_{\mathrm{policy}} = -\mathcal{L}^{\mathrm{CLIP}}(\theta)
$$

Ý tưởng của PPO là:

- nếu policy mới thay đổi vừa phải, cập nhật được chấp nhận
- nếu policy mới thay đổi quá mạnh, toán hạng `clip` sẽ chặn bớt lợi ích cập nhật

Điều này làm PPO ổn định và phù hợp với các bài toán như macro placement, nơi một policy xấu có thể nhanh chóng đưa agent vào vùng hành động kém chất lượng.

Trong dự án:

- baseline dùng `MaskablePPO + MLP`
- nhánh chính dùng PPO cho model graph-based AlphaChip-like

### 6.16 Liên hệ trực tiếp với bài toán macro placement

Việc ánh xạ từ RL sang macro placement trong đồ án có thể tóm tắt bằng bảng sau:

| Khái niệm RL | Ý nghĩa trong DATN |
|---|---|
| Trạng thái $s_t$ | netlist graph, current macro, occupancy, mask, metadata |
| Hành động $a_t$ | chọn một grid cell để đặt macro hiện tại |
| Reward $r_t$ | mức cải thiện của proxy cost hoặc terminal proxy gain |
| Episode | đặt xong toàn bộ hoặc một số hard macro mục tiêu |
| Policy $\pi_\theta$ | mạng quyết định vị trí placement |
| Value function $V_\phi$ | ước lượng chất lượng placement kỳ vọng từ trạng thái hiện tại |

Nhờ cách mô hình hóa này, bài toán placement trở thành một chuỗi quyết định có thể học được thay vì chỉ là một bài toán tối ưu tĩnh.

---

## Chương 7. AlphaChip, Circuit Training và hướng tiếp cận của DATN

### 7.1 AlphaChip / Circuit Training là gì

Google Circuit Training là framework RL cho macro placement. Ý tưởng nổi bật:

- biểu diễn thiết kế như một netlist có cấu trúc đồ thị
- gridding canvas để giảm không gian hành động
- đặt hard macro tuần tự
- dùng proxy cost để huấn luyện
- dùng clustering/grouping để biểu diễn logic lớn gọn hơn

### 7.2 Điều gì không public đầy đủ

Theo tài liệu trong repo, môi trường hiện tại **không nên giả định** có:

- `plc_wrapper_main` dùng được
- backend cost production của Google
- hạ tầng distributed training nội bộ
- full AlphaChip system

Do đó DATN chủ trương:

```text
không cố chạy AlphaChip full
-> xây AlphaChip-like flow open-source
```

### 7.3 Hướng của DATN

Dự án tách thành hai lớp:

1. **Baseline đơn giản**
- `MaskablePPO`
- quan sát vector ngắn
- mục tiêu xác nhận pipeline end-to-end

2. **Hướng nghiên cứu chính**
- graph observation
- sparse adjacency
- current macro attention
- actor-critic gần tinh thần Circuit Training hơn

---

## Chương 8. Kiến trúc tổng thể của repo

Các thư mục chính:

- `MacroPlacement`
- `DREAMPlace`
- `rl_macroplacement_agent`
- `Quy_trinh`
- `tools`

### 8.1 `MacroPlacement`

Đây là khối rất quan trọng. Nó cung cấp:

- benchmark hiện đại có macro thật
- docs về Circuit Training code elements
- proxy cost implementation
- format translators
- flow scripts
- testcases và enablements

### 8.2 `DREAMPlace`

Dùng làm baseline placement gradient-based để đối chiếu với RL.

### 8.3 `rl_macroplacement_agent`

Là phần code mới của đồ án:

- environment RL
- scripts train/eval
- AlphaChip-like features/model/agent
- chuyển đổi placement
- compare result

### 8.4 `Quy_trinh`

Lưu lộ trình triển khai theo milestone, giúp định vị rõ:

- milestone nào là EDA
- milestone nào là dữ liệu
- milestone nào là RL
- milestone nào là đưa kết quả quay lại OpenROAD

### 8.5 `tools`

Hiện có tiện ích như `openroad-remote-gui` để xem checkpoint từ xa qua VNC.

---

## Chương 9. Các thành phần kỹ thuật chính trong `MacroPlacement`

Theo docs trong repo, các code elements quan trọng nhất là:

- `Gridding`
- `Grouping`
- `Clustering`
- `FormatTranslators`
- `Plc_client`
- `FDPlacement`
- `SimulatedAnnealing`

### 9.1 Gridding

Mục tiêu:

- chia canvas thành `n_rows x n_cols`
- giảm không gian hành động cho RL
- tạo hệ lưới ổn định cho đặt macro

Trong Circuit Training style, grid được chọn bằng cách cân bằng:

- số ô lưới
- aspect ratio ô
- khả năng pack macro
- mức lãng phí không gian

### 9.2 Grouping

Mục tiêu:

- gom macro pins của cùng macro
- gom IO gần nhau thành cluster
- gom standard cells có liên hệ gần nhau với macro hoặc IO cluster

Tác dụng:

- tạo cấu trúc logic tốt hơn cho bước clustering
- giúp soft macro phản ánh kết nối hữu ích hơn

### 9.3 Hypergraph clustering

Mục tiêu:

- gom hàng triệu standard cells thành vài nghìn cluster
- giảm kích thước bài toán
- phục vụ placement xấp xỉ nhanh

Trong tài liệu repo, clustering là phần rất quan trọng để tiến gần hơn tới Circuit Training.

### 9.4 Format translators

Hỗ trợ các hướng đổi format:

- `LEF/DEF -> Protobuf`
- `Bookshelf -> Protobuf`
- `Bookshelf -> LEF/DEF -> Protobuf`
- `Protobuf -> LEF/DEF`

Đây là cầu nối giữa:

- thế giới EDA truyền thống
- dữ liệu RL kiểu Circuit Training

### 9.5 Plc_client / PlacementCost

Đây là implementation open-source thay cho phần evaluator kiểu black-box.

Nó hỗ trợ:

- `get_cost()`
- `get_wirelength()`
- `get_density_cost()`
- `get_congestion_cost()`

Vai trò của nó là cực kỳ trung tâm vì reward và đánh giá placement đều phụ thuộc vào đây.

### 9.6 FD Placement

Force-directed placement dùng để đặt soft macro/cluster nhanh để hỗ trợ đánh giá.

### 9.7 Simulated Annealing

Repo `MacroPlacement` cũng cung cấp baseline SA. Điều này rất quan trọng về mặt học thuật vì RL không phải baseline duy nhất cần so sánh.

---

## Chương 10. `rl_macroplacement_agent`: phần RL mà dự án tự xây

Thư mục này chứa pipeline RL nhẹ, không phụ thuộc trực tiếp vào full Circuit Training.

Các script chính:

- `macro_env.py`
- `train_maskable_ppo.py`
- `evaluate_policy.py`
- `eval_proxy.py`
- `plc_utils.py`
- `plc_to_openroad_tcl.py`
- `inspect_dataset.py`
- `alphachip_like_features.py`
- `alphachip_like_model.py`
- `alphachip_like_agent.py`
- `train_alphachip_like_ppo.py`
- `evaluate_alphachip_like_policy.py`
- `run_dreamplace_baseline.py`
- `convert_bookshelf_pl_to_plc.py`
- `compare_results.py`

### 10.1 Baseline đơn giản

Baseline đầu tiên dùng:

- observation vector ngắn
- action masking
- PPO kiểu MLP

Mục tiêu không phải là đạt SOTA mà là xác nhận:

```text
train -> eval -> xuất .plc -> chấm proxy -> so sánh
```

### 10.2 Nhánh AlphaChip-like

Nhánh này cố tiến gần hơn tới Circuit Training bằng:

- metadata encoder
- node features
- sparse graph edges
- current-node attention
- grid policy head
- value head

### 10.3 Tiện ích thao tác `.plc`

`plc_utils.py` đọc và sửa file `.plc` mà vẫn giữ comment/format gốc. Điều này hữu ích cho:

- sinh placement mới
- cập nhật node position
- xuất `.plc` để chấm tiếp

### 10.4 Chuyển đổi sang OpenROAD Tcl

`plc_to_openroad_tcl.py` dùng để đổi placement Tcl dạng `placeInstance` sang cú pháp phù hợp với OpenROAD:

- `place_inst`
- hoặc `place_macro`

Đây là mắt xích quan trọng của milestone đưa RL quay lại backend vật lý.

---

## Chương 11. Pipeline end-to-end của DATN

Pipeline tổng thể của dự án có thể viết ngắn gọn như sau:

```text
RTL / benchmark
    -> synthesis / physical baseline
    -> dữ liệu netlist + placement
    -> format translation
    -> netlist.pb.txt + initial.plc
    -> RL environment
    -> huấn luyện PPO / AlphaChip-like PPO
    -> best_rl.plc
    -> convert sang Tcl / OpenROAD
    -> chạy lại backend vật lý
    -> đánh giá QoR
```

### 11.1 Chặng EDA nền

OpenROAD-flow-scripts chạy thiết kế mẫu để xác nhận:

- synthesis chạy được
- floorplan chạy được
- placement/cts/route tạo checkpoint được

### 11.2 Chặng dữ liệu RL

`MacroPlacement` cung cấp benchmark đã chuẩn hóa như:

- `ariane133`
- `ariane136`
- `nvdla`
- `mempool`

Testcase được ưu tiên trong repo hiện tại là:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

### 11.3 Chặng RL

Input:

- `netlist.pb.txt`
- `initial.plc`

Output:

- model checkpoint
- file placement `.plc`
- metric JSON

### 11.4 Chặng re-evaluation

Placement đầu ra được:

- convert về Tcl
- nạp lại OpenROAD
- refine/evaluate
- so sánh với baseline

---

## Chương 12. Proxy cost, reward và các metric đánh giá

### 12.1 Proxy cost là gì

Trong Circuit Training style, proxy cost là tổng có trọng số của:

- wirelength cost
- density cost
- congestion cost

Tổng quát:

```text
proxy_cost =
    W_wirelength * cost_wirelength
  + W_density * cost_density
  + W_congestion * cost_congestion
```

### 12.2 Wirelength cost

Dựa trên HPWL:

- tính bbox của từng net
- cộng `(xmax - xmin) + (ymax - ymin)`
- có thể nhân theo weight của source pin
- chuẩn hóa theo kích thước canvas và net count

### 12.3 Density cost

Dựa trên occupancy của grid cells:

- chia canvas thành grid
- tính mật độ mỗi ô
- lấy top 10% ô dày nhất
- lấy trung bình rồi nhân hệ số

### 12.4 Congestion cost

Dựa trên congestion ngang và dọc:

- ước lượng congestion do routing
- cộng congestion do macro
- có smoothing
- lấy top 5% cell congested nhất

### 12.5 Thực tế trong repo này

Theo tài liệu milestone và config:

- `get_cost()` là chỉ số chính
- `get_congestion_cost()` có thể không ổn định trong một số trường hợp
- baseline reward thường ưu tiên cost hoặc wirelength-based proxy

### 12.6 Metric cuối cùng cần quan tâm

Proxy cost tốt là cần thiết nhưng chưa đủ. Đánh giá nghiên cứu tốt nên xét thêm:

- routed wirelength
- congestion thật
- WNS
- TNS
- power
- route success
- runtime

---

## Chương 13. Các định dạng file trong dự án và ý nghĩa của chúng

Đây là phần rất quan trọng vì DATN là dự án nối nhiều công cụ với nhau.

### 13.1 RTL và mô tả logic

#### `.v`

- Verilog
- dùng cho RTL hoặc gate-level netlist
- đầu vào synthesis hoặc đầu ra synthesis

#### `.sv`

- SystemVerilog
- mô tả RTL hiện đại hơn Verilog

#### `.vcd`

- waveform mô phỏng
- dùng để debug chức năng khi verify RTL

### 13.2 Thư viện và công nghệ

#### `.lib`

- Liberty timing/power library
- chứa delay, slew, area, power của cell
- synthesis và timing analysis phụ thuộc nhiều vào file này

#### `.lef`

- Library Exchange Format
- mô tả hình học cell/macro, layer, obstruction, pin shape
- dùng cho placement/routing

### 13.3 Physical design và checkpoint

#### `.def`

- Design Exchange Format
- mô tả placement, pins, nets, floorplan, routing từng giai đoạn
- là format trao đổi vật lý rất phổ biến

#### `.odb`

- OpenDB database của OpenROAD
- checkpoint nội bộ, rất tiện để mở GUI hoặc chạy tiếp flow

#### `.guide`

- global routing guide
- dùng ở giai đoạn routing

#### `.spef`

- Standard Parasitic Exchange Format
- chứa parasitic sau routing
- phục vụ timing/power chính xác hơn

#### `.sdc`

- Synopsys Design Constraints
- clock, IO delay, exceptions, timing constraints

### 13.4 Dữ liệu RL / Circuit Training style

#### `netlist.pb.txt`

- protobuf text-format của netlist
- format trung tâm cho môi trường RL
- chứa nodes, inputs, attributes, geometry, types, connectivity

#### `.plc`

- placement canvas / placement solution cho Circuit Training style
- có metadata grid, canvas, metrics và danh sách `node_index x y orientation fixed`

### 13.5 Flow control và config

#### `.tcl`

- script điều khiển tool
- dùng để chạy flow hoặc nạp placement

#### `.yaml`

- file cấu hình thí nghiệm RL

#### `.json`

- lưu config, metrics, summary, output comparison

### 13.6 Bookshelf và benchmark placement cổ điển

Nhóm file này xuất hiện khi làm việc với DREAMPlace hoặc benchmark cổ điển:

#### `.aux`

- file gốc chỉ ra bộ file Bookshelf đi kèm

#### `.nodes`

- danh sách node và kích thước

#### `.nets`

- mô tả connectivity

#### `.pl`

- placement result theo Bookshelf

#### `.scl`

- row/site information

#### `.wts`

- weight thông tin cho node/net

### 13.7 File hỗ trợ clustering/grouping

#### `.fix`

- ràng buộc group/partition cho clustering
- dùng làm input cho hMETIS hoặc bước gom cluster

---

## Chương 14. Giải thích trực tiếp hai format quan trọng nhất: `.pb.txt` và `.plc`

### 14.1 `netlist.pb.txt`

Từ file mẫu trong repo có thể thấy mỗi `node` chứa:

- `name`
- `input`
- `attr`

Một `attr` có `key` và `value`, ví dụ:

- `type`
- `side`
- `x`
- `y`
- `width`
- `height`
- `orientation`
- `macro_name`
- `ref_name`

Ý nghĩa:

- `PORT`: cổng IO trên biên chip
- `MACRO`: hard macro
- `MACRO_PIN`: pin thuộc macro
- `SOFT_MACRO`: cluster logic mềm

File này đồng thời mô tả:

- connectivity của netlist
- hình học tương đối
- thông tin placement ban đầu
- cấu trúc cần thiết để tính cost

Đây là **biểu diễn đồ thị trung gian** giữa EDA truyền thống và RL environment.

### 14.2 `.plc`

File `.plc` mẫu trong repo có hai phần chính.

#### Phần comment header

Bao gồm các metadata như:

- source netlist
- số cột và số hàng grid
- width, height canvas
- area
- wirelength
- wirelength cost
- congestion cost
- density cost
- routes per micron
- smoothing factor
- count các loại node

Phần này cực hữu ích vì nó cho biết:

- không gian placement
- lưới hành động
- các chỉ số baseline
- quy mô bài toán

#### Phần node placement

Dòng tiêu đề:

```text
# node_index x y orientation fixed
```

Mỗi dòng sau đó là:

```text
node_index x y orientation fixed
```

Ý nghĩa:

- `node_index`: id node trong netlist
- `x`, `y`: tọa độ tâm hoặc tọa độ placement
- `orientation`: hướng đặt macro/cell
- `fixed`: có cố định hay không

Đây là format mà agent RL cập nhật khi tạo ra placement mới.

### 14.3 Quan hệ giữa `.pb.txt` và `.plc`

- `.pb.txt` mô tả **đồ thị + hình học + connectivity**
- `.plc` mô tả **trạng thái placement cụ thể trên canvas**

Hai file này đi cùng nhau gần như trong mọi thí nghiệm RL của repo.

---

## Chương 15. Công cụ open-source thay thế Genus, Innovus và các tool thương mại

### 15.1 Bảng thay thế chính

| Tool thương mại / thành phần | Thay thế open-source trong DATN | Vai trò |
|---|---|---|
| `Cadence Genus` | `Yosys` | synthesis RTL -> gate netlist |
| `Cadence Innovus` | `OpenROAD` + `OpenROAD-flow-scripts` | floorplan, placement, CTS, routing |
| `plc_wrapper_main` | `plc_client_os` | placement cost evaluator |
| AlphaChip RL infra | `Gymnasium` + `stable-baselines3` + `sb3-contrib` | huấn luyện RL |
| commercial global placer | `DREAMPlace` | baseline placement gradient-based |
| signoff GUI/viewer | `OpenROAD GUI`, `KLayout` | xem checkpoint/layout |
| logic simulation tool thương mại | `iverilog`, `verilator` | verify RTL |
| layout utility | `Magic`, `Netgen` | hỗ trợ physical/lvs-style workflow |

### 15.2 Yosys thay Genus

Yosys phù hợp cho:

- synthesis cơ bản
- kiểm thử flow open-source
- tạo gate netlist để đi tiếp sang backend vật lý

Điểm mạnh:

- dễ cài
- cộng đồng mạnh
- tích hợp tốt với ORFS

Điểm yếu:

- không thay hoàn toàn capability của Genus trong mọi flow công nghiệp
- physical-aware synthesis và QoR cao cấp còn hạn chế hơn tool thương mại

### 15.3 OpenROAD thay Innovus

OpenROAD hiện là backend vật lý open-source mạnh nhất trong ngữ cảnh này.

Nó hỗ trợ:

- floorplan
- macro placement hooks
- standard-cell placement
- CTS
- global routing
- detailed routing
- OpenDB checkpoint

Điểm mạnh:

- tích hợp thành flow rõ ràng
- phù hợp nghiên cứu
- có GUI và checkpoint `.odb`

Điểm yếu:

- tương thích version cần chú ý
- QoR và độ trưởng thành chưa tương đương hoàn toàn flow thương mại ở mọi thiết kế

### 15.4 plc_client_os thay cost engine đóng

Đây là thay thế rất quan trọng vì không có evaluator ổn định thì RL gần như không làm được.

### 15.5 DREAMPlace

DREAMPlace không thay toàn bộ Innovus/OpenROAD. Nó chỉ thay vai trò:

- global placement baseline
- đối chứng với RL

### 15.6 OpenLane có dùng được không

Có thể cân nhắc `OpenLane` hoặc `OpenLane2` cho một số flow RTL-to-GDS mở, nhưng trong repo này trọng tâm đang là:

- `OpenROAD`
- `ORFS`
- `MacroPlacement`
- `DREAMPlace`

nên đó mới là stack sát hiện trạng nhất.

---

## Chương 16. Hướng dẫn sử dụng stack open-source trong đồ án

### 16.1 Luồng tối thiểu đã được xác nhận

1. Dựng OpenROAD và ORFS
2. Dùng `Yosys` làm synthesis
3. Chạy flow mẫu `nangate45/gcd`
4. Xác nhận tạo được checkpoint `.odb`, `.def`, `.spef`
5. Dùng benchmark macro thật từ `MacroPlacement`
6. Kiểm tra `netlist.pb.txt`, `initial.plc`, `legalized.plc`
7. Train agent RL
8. Sinh `best_rl.plc`
9. Convert placement sang Tcl/OpenROAD
10. Đánh giá lại bằng backend vật lý

### 16.2 Bộ benchmark nên ưu tiên

Theo tài liệu repo, **không nên dùng `gcd` để học macro placement** vì nó không có macro thật.

Benchmark nên ưu tiên:

- `ariane133`
- `ariane136`
- `nvdla`
- `mempool`

### 16.3 Bộ dữ liệu đầu tiên nên dùng

Đường dẫn thực tế trong repo:

```text
MacroPlacement/Flows/NanGate45/ariane133/netlist/output_CT_Grouping/
```

Cần có:

- `netlist.pb.txt`
- `initial.plc`
- `legalized.plc`

### 16.4 Cách chấm proxy

Script dùng trong repo:

- `rl_macroplacement_agent/scripts/eval_proxy.py`

Input:

- netlist
- plc

Output:

- JSON metric

### 16.5 Cách convert placement sang OpenROAD

Quy trình:

1. dùng converter tạo Tcl từ `.plc`
2. đổi dialect nếu cần bằng `plc_to_openroad_tcl.py`
3. nạp vào OpenROAD

---

## Chương 17. DREAMPlace trong dự án này đóng vai trò gì

DREAMPlace là một placer tối ưu hóa liên tục dựa trên gradient. Trong đồ án này nó được dùng làm:

- **baseline đối chứng**
- không phải agent RL
- không phải backend vật lý hoàn chỉnh

Pipeline so sánh là:

```text
DREAMPlace output .pl
    -> convert sang .plc
    -> dùng cùng PlacementCost để chấm
    -> so sánh công bằng với PPO / AlphaChip-like PPO
```

Ý nghĩa học thuật:

- giúp kiểm tra RL có thực sự đem lại lợi ích hay không
- tránh việc chỉ so với `initial.plc`
- cho phép đặt RL cạnh một baseline tối ưu hóa truyền thống

---

## Chương 18. Milestone và trạng thái hiện tại của DATN

### 18.1 Milestone 1: dựng nền EDA open-source

Mục tiêu:

- thay flow thương mại bằng stack open-source
- chạy được baseline physical design

Artifact mong muốn:

- `1_synth.*`
- `2_floorplan.*`
- `3_place.*`
- `6_final.odb`
- `6_final.def`
- `6_final.sdc`
- `6_final.v`
- `6_final.spef`

### 18.2 Milestone 2: chuẩn hóa dữ liệu cho RL

Mục tiêu:

- chọn benchmark có macro thật
- kiểm tra `netlist.pb.txt`, `initial.plc`, `legalized.plc`
- xác nhận proxy evaluator chạy được

### 18.3 Milestone 3: xây RL loop open-source

Mục tiêu:

- dùng `plc_client_os` + `Gymnasium` + `SB3`
- train baseline PPO
- tạo baseline DREAMPlace
- phát triển nhánh AlphaChip-like

### 18.4 Milestone 4: quay placement về OpenROAD

Mục tiêu:

- convert `.plc` sang Tcl
- load lại vào OpenROAD
- refine/evaluate
- so sánh proxy với QoR vật lý

### 18.5 Trạng thái hiện tại rút ra từ repo

Những điểm đã khá rõ:

- pipeline open-source là hướng chính
- baseline RL đã chạy được
- nhánh AlphaChip-like đã có feature/model/trainer
- OpenROAD/ORFS đã được xác nhận tới mức tạo checkpoint cuối
- `ariane133` là testcase trung tâm hiện tại
- DREAMPlace đã được tích hợp như baseline độc lập

---

## Chương 19. Khuyến nghị nghiên cứu và mở rộng

### 19.1 Hướng ngắn hạn

- hoàn thiện so sánh nhiều seed cho PPO và AlphaChip-like PPO
- đưa placement đầu ra quay lại OpenROAD cho testcase macro thật
- so sánh `initial`, `legalized`, `PPO`, `AlphaChip-like PPO`, `DREAMPlace`, `SA`

### 19.2 Hướng trung hạn

- cải tiến observation graph
- thêm curriculum learning
- tinh chỉnh reward terminal vs stepwise
- xử lý congestion cost ổn định hơn
- mở rộng sang nhiều benchmark

### 19.3 Hướng dài hạn

- đánh giá cross-design generalization
- đưa thêm timing-aware reward
- kết hợp RL với analytical placement
- so sánh với simulated annealing từ `MacroPlacement`

### 19.4 Những điều cần thận trọng

- không nên tuyên bố RL tốt hơn chỉ dựa vào proxy cost
- cần phân biệt rõ baseline demo và hướng nghiên cứu chính
- cần nhấn mạnh rằng stack hiện tại là **open-source AlphaChip-like**, không phải full AlphaChip production

---

## Chương 20. Kết luận

DATN là một dự án nối ba thế giới:

- **thiết kế vi mạch số / VLSI**
- **EDA physical design**
- **học tăng cường cho tối ưu placement**

Giá trị lớn nhất của repo không nằm ở một script riêng lẻ, mà ở việc nó ghép thành công một **chuỗi nghiên cứu hoàn chỉnh**:

```text
EDA open-source
    + benchmark macro thật
    + format translators
    + proxy evaluator
    + RL environment
    + baseline DREAMPlace
    + OpenROAD re-evaluation
```

Nếu nhìn như một hệ thống, ý nghĩa của từng khối là:

- `MacroPlacement`: cung cấp benchmark, docs, translator, evaluator
- `rl_macroplacement_agent`: cung cấp RL pipeline của đồ án
- `DREAMPlace`: cung cấp baseline tối ưu hóa gradient-based
- `OpenROAD/ORFS`: cung cấp backend vật lý để kiểm chứng placement
- `Quy_trinh`: cung cấp bản đồ triển khai theo milestone

Từ góc nhìn học thuật, đồ án này đang đi theo hướng đúng:

- không phụ thuộc tool thương mại
- không phụ thuộc backend đóng
- có khả năng tái lập
- có baseline để so sánh
- có cầu nối từ RL quay lại physical design thật

Đó chính là nền tảng phù hợp để tiếp tục phát triển thành báo cáo, luận văn hoặc bài nghiên cứu hoàn chỉnh.

---

## Phụ lục A. Tóm tắt nhanh các file/format quan trọng nhất

| Format | Mục đích chính |
|---|---|
| `.v`, `.sv` | RTL hoặc gate-level netlist |
| `.lib` | timing/power library |
| `.lef` | hình học công nghệ, cell, macro |
| `.def` | floorplan, placement, routing exchange |
| `.odb` | checkpoint OpenROAD/OpenDB |
| `.sdc` | timing constraints |
| `.spef` | parasitics |
| `.guide` | guide cho global routing |
| `netlist.pb.txt` | graph/netlist kiểu Circuit Training |
| `.plc` | placement solution / placement state |
| `.tcl` | script điều khiển tool |
| `.yaml` | config thí nghiệm |
| `.json` | metrics, summary, kết quả |
| `.pl` | placement output kiểu Bookshelf/DREAMPlace |
| `.aux/.nodes/.nets/.scl/.wts` | bộ benchmark Bookshelf |
| `.fix` | ràng buộc grouping/clustering |

## Phụ lục B. Tóm tắt tool open-source nên nhớ

| Tool | Vai trò |
|---|---|
| `Yosys` | synthesis |
| `OpenROAD` | physical design backend |
| `OpenROAD-flow-scripts` | flow wrapper cho OpenROAD |
| `DREAMPlace` | baseline placer |
| `iverilog`, `verilator` | verify RTL |
| `KLayout` | layout viewer |
| `Magic`, `Netgen` | utility/layout verification support |
| `Gymnasium` | RL environment interface |
| `stable-baselines3` | RL algorithms |
| `sb3-contrib` | MaskablePPO |
| `plc_client_os` | proxy evaluator |
