---
title: "CHƯƠNG 1. CƠ SỞ LÝ THUYẾT VỀ HỌC TĂNG CƯỜNG"
lang: vi
---

# 1.1. Giới thiệu

Trong những năm gần đây, trí tuệ nhân tạo và học máy đã trở thành một trong những hướng nghiên cứu quan trọng của khoa học máy tính. Bên cạnh học có giám sát và học không giám sát, học tăng cường là một mô hình học đặc biệt, trong đó tác nhân học cách ra quyết định thông qua quá trình tương tác liên tục với môi trường. Khác với các bài toán học truyền thống, học tăng cường không nhận được bộ dữ liệu gán nhãn cố định ngay từ đầu, mà phải tự tìm cách hành động để tối đa hóa lợi ích tích lũy trong tương lai.

Học tăng cường đã đạt được nhiều thành tựu nổi bật trong các lĩnh vực như chơi game, điều khiển robot, điều phối tài nguyên, tối ưu hệ thống và gần đây là thiết kế vi mạch. Đối với các bài toán có tính chất ra quyết định tuần tự, không gian tìm kiếm lớn và có nhiều ràng buộc phức tạp, học tăng cường là một hướng tiếp cận có giá trị cả về mặt lý thuyết lẫn thực nghiệm.

Trong phạm vi đồ án tốt nghiệp này, học tăng cường được nghiên cứu như một nền tảng phương pháp luận để giải bài toán macro placement trong thiết kế vi mạch số. Vì vậy, việc trình bày đầy đủ cơ sở lý thuyết, mục tiêu, các khái niệm cốt lõi và các công thức toán học của học tăng cường là rất cần thiết để làm nền tảng cho các chương tiếp theo.

# 1.2. Mục đích và mục tiêu của chương

Chương này được xây dựng với các mục đích chính sau đây:

- Trình bày tổng quan và có hệ thống về học tăng cường.
- Giải thích các khái niệm cốt lõi như agent, environment, state, action, reward và policy.
- Trình bày mô hình toán học của bài toán học tăng cường dưới dạng Markov Decision Process.
- Giới thiệu các hàm giá trị, phương trình Bellman và ý nghĩa của chúng.
- Trình bày các hướng thuật toán nền tảng trong học tăng cường như value-based, policy-based và actor-critic.
- Trình bày cơ sở lý thuyết của PPO, là thuật toán được sử dụng trong hướng nghiên cứu của đồ án.
- Làm rõ mối liên hệ giữa học tăng cường và bài toán macro placement trong thiết kế vi mạch.

Về mặt nội dung, chương này hướng tới các mục tiêu cụ thể:

1. Hiểu được cách mô hình hóa bài toán tối ưu thành bài toán ra quyết định tuần tự.
2. Hiểu được cách agent học từ phần thưởng thay vì học từ nhãn có sẵn.
3. Hiểu được các hàm mục tiêu toán học trong học tăng cường.
4. Lựa chọn được nhóm thuật toán phù hợp với bài toán của đồ án.
5. Xây dựng được cầu nối giữa lý thuyết học tăng cường và bài toán thực tế trong EDA.

# 1.3. Khái niệm tổng quát về học tăng cường

Học tăng cường là một mô hình học trong đó một tác nhân, gọi là *agent*, tương tác với môi trường, gọi là *environment*, để học cách chọn hành động sao cho tổng phần thưởng nhận được trong tương lai là lớn nhất. Ở mỗi thời điểm, agent quan sát trạng thái hiện tại của môi trường, đưa ra một hành động, sau đó môi trường chuyển sang trạng thái mới và trả về một mức phần thưởng. Quá trình này được lặp lại liên tục cho đến khi kết thúc một episode hoặc đạt một điều kiện dừng nhất định.

Chu trình học tăng cường có thể mô tả như sau:

- Agent nhận trạng thái hiện tại $s_t$.
- Agent chọn hành động $a_t$.
- Môi trường cập nhật sang trạng thái mới $s_{t+1}$.
- Môi trường trả về phần thưởng $r_{t+1}$.
- Agent sử dụng thông tin vừa thu được để điều chỉnh chính sách hành động.

# 1.4. Các thành phần cơ bản của học tăng cường

## 1.4.1. Agent

Agent là thực thể thực hiện hành động trong môi trường. Agent có trách nhiệm thu nhận thông tin, đưa ra quyết định và cải thiện chiến lược hành động thông qua quá trình học. Trong nhiều bài toán hiện đại, agent được biểu diễn bởi một mô hình học máy hoặc một mạng nơ-ron sâu.

## 1.4.2. Environment

Environment là hệ thống mà agent tương tác. Môi trường nhận hành động từ agent, cập nhật trạng thái và trả về phần thưởng. Trong bài toán macro placement, environment có thể được hiểu là bộ mô phỏng trạng thái placement kết hợp với bộ đánh giá chi phí placement.

## 1.4.3. State

State là biểu diễn của tình trạng hiện tại của môi trường tại thời điểm $t$. Trạng thái cần chứa đủ thông tin để agent có thể đưa ra quyết định phù hợp. Chất lượng của biểu diễn trạng thái ảnh hưởng trực tiếp đến khả năng học của agent.

## 1.4.4. Action

Action là hành động mà agent có thể lựa chọn tại một trạng thái. Tập tất cả các hành động khả thi được gọi là action space. Tùy bài toán, action space có thể rời rạc hoặc liên tục.

## 1.4.5. Reward

Reward là tín hiệu phản hồi từ môi trường, cho biết hành động vừa thực hiện tốt hay xấu theo mục tiêu tối ưu. Agent không tối ưu từng reward đơn lẻ, mà tối ưu tổng reward tích lũy trong suốt quá trình tương tác.

## 1.4.6. Policy

Policy là quy tắc mà agent sử dụng để chọn hành động dựa trên trạng thái. Đây là đối tượng trung tâm của học tăng cường, vì toàn bộ mục tiêu của việc học là tìm được một policy cho phép agent đạt hiệu quả cao nhất.

# 1.5. Mô hình Markov Decision Process

Một bài toán học tăng cường thường được mô hình hóa bởi Markov Decision Process, viết tắt là MDP. Đây là khung toán học tiêu chuẩn để mô tả quá trình ra quyết định tuần tự trong điều kiện không chắc chắn:

$$
\mathcal{M} = (\mathcal{S}, \mathcal{A}, P, R, \gamma)
$$

Trong đó:

- $\mathcal{S}$ là tập trạng thái.
- $\mathcal{A}$ là tập hành động.
- $P(s' \mid s, a)$ là xác suất chuyển trạng thái.
- $R(s, a)$ hoặc $R(s, a, s')$ là hàm phần thưởng.
- $\gamma$ là hệ số chiết khấu, với $0 \le \gamma < 1$.

## 1.5.1. Tính chất Markov

Tính chất Markov phát biểu rằng xác suất chuyển trạng thái trong tương lai chỉ phụ thuộc vào trạng thái hiện tại và hành động hiện tại, không phụ thuộc trực tiếp vào toàn bộ lịch sử quá khứ:

$$
P(s_{t+1} \mid s_t, a_t, \dots, s_0, a_0) = P(s_{t+1} \mid s_t, a_t)
$$

# 1.6. Mục tiêu tối ưu trong học tăng cường

Mục tiêu của agent là tối đa hóa tổng phần thưởng tích lũy theo thời gian. Đại lượng này được gọi là return:

$$
G_t = \sum_{k=0}^{\infty} \gamma^k r_{t+k+1}
$$

Nếu episode hữu hạn có độ dài $T$, return có thể viết dưới dạng:

$$
G_t = r_{t+1} + \gamma r_{t+2} + \gamma^2 r_{t+3} + \cdots + \gamma^{T-t-1} r_T
$$

Hệ số chiết khấu $\gamma$ quyết định mức độ quan tâm của agent đối với phần thưởng trong tương lai. Giá trị $\gamma$ càng lớn, agent càng chú ý đến lợi ích dài hạn.

Hàm mục tiêu tổng quát của policy có tham số $\theta$ thường được viết:

$$
J(\theta) = \mathbb{E}_{\pi_\theta}[G_t]
$$

# 1.7. Chính sách và hàm giá trị

## 1.7.1. Policy

Policy mô tả xác suất chọn hành động tại một trạng thái nhất định:

$$
\pi(a \mid s) = \Pr(A_t = a \mid S_t = s)
$$

Nếu policy được tham số hóa bằng mạng nơ-ron:

$$
\pi_\theta(a \mid s)
$$

## 1.7.2. State-value function

Hàm giá trị trạng thái cho biết trạng thái $s$ tốt đến mức nào nếu agent tiếp tục hành động theo policy $\pi$:

$$
V^\pi(s) = \mathbb{E}_\pi[G_t \mid S_t = s]
$$

## 1.7.3. Action-value function

Hàm giá trị hành động cho biết việc chọn hành động $a$ tại trạng thái $s$ có lợi đến mức nào:

$$
Q^\pi(s, a) = \mathbb{E}_\pi[G_t \mid S_t = s, A_t = a]
$$

## 1.7.4. Advantage function

Advantage đo mức chênh lệch giữa giá trị của một hành động so với giá trị trung bình tại trạng thái đó:

$$
A^\pi(s, a) = Q^\pi(s, a) - V^\pi(s)
$$

Nếu advantage dương, hành động đó tốt hơn mức trung bình. Nếu advantage âm, hành động đó kém hơn mức trung bình.

# 1.8. Phương trình Bellman

Phương trình Bellman là một trong những kết quả quan trọng nhất của học tăng cường. Nó mô tả mối liên hệ đệ quy giữa giá trị hiện tại và giá trị tương lai.

## 1.8.1. Bellman expectation equation cho state-value

$$
V^\pi(s) =
\sum_a \pi(a \mid s)\sum_{s',r} P(s', r \mid s,a)\left[r + \gamma V^\pi(s')\right]
$$

## 1.8.2. Bellman expectation equation cho action-value

$$
Q^\pi(s,a) =
\sum_{s',r} P(s', r \mid s,a)\left[r + \gamma \sum_{a'} \pi(a' \mid s')Q^\pi(s',a')\right]
$$

## 1.8.3. Bellman optimality equation

$$
V^*(s) =
\max_a \sum_{s',r} P(s', r \mid s,a)\left[r + \gamma V^*(s')\right]
$$

$$
Q^*(s,a) =
\sum_{s',r} P(s', r \mid s,a)\left[r + \gamma \max_{a'} Q^*(s',a')\right]
$$

# 1.9. Vấn đề khám phá và khai thác

Một trong những thách thức cốt lõi của học tăng cường là cân bằng giữa khám phá và khai thác. Khám phá là thử những hành động mới để tìm nghiệm tốt hơn, còn khai thác là tận dụng những gì agent đã học được để tối đa hóa kết quả hiện tại. Hai yếu tố này cần được cân bằng hợp lý trong suốt quá trình học.

# 1.10. Các nhóm thuật toán học tăng cường

Về tổng quan, các thuật toán học tăng cường có thể chia thành ba nhóm lớn:

- Phương pháp dựa trên giá trị.
- Phương pháp dựa trên chính sách.
- Phương pháp actor-critic.

## 1.10.1. Phương pháp dựa trên giá trị

Phương pháp này tập trung học hàm giá trị, thường là hàm $Q$, sau đó suy ra policy tốt nhất từ hàm giá trị đã học.

### Q-learning

$$
Q(s_t, a_t) \leftarrow
Q(s_t, a_t) + \alpha \left[r_{t+1} + \gamma \max_a Q(s_{t+1}, a) - Q(s_t, a_t)\right]
$$

### SARSA

$$
Q(s_t, a_t) \leftarrow
Q(s_t, a_t) + \alpha \left[r_{t+1} + \gamma Q(s_{t+1}, a_{t+1}) - Q(s_t, a_t)\right]
$$

## 1.10.2. Phương pháp dựa trên chính sách

Phương pháp này tối ưu trực tiếp policy thay vì học hàm giá trị rồi mới suy ra policy.

$$
\nabla_\theta J(\theta) =
\mathbb{E}_{\pi_\theta}
\left[\nabla_\theta \log \pi_\theta(a_t \mid s_t)\, Q^{\pi_\theta}(s_t, a_t)\right]
$$

Nếu dùng advantage:

$$
\nabla_\theta J(\theta) =
\mathbb{E}_{\pi_\theta}
\left[\nabla_\theta \log \pi_\theta(a_t \mid s_t)\, A^{\pi_\theta}(s_t, a_t)\right]
$$

## 1.10.3. Phương pháp actor-critic

Actor-critic kết hợp ưu điểm của hai hướng trên. Actor học policy, critic học hàm giá trị để đánh giá và hỗ trợ actor cập nhật ổn định hơn.

$$
\mathcal{L}_{actor} = -\mathbb{E}\left[\log \pi_\theta(a_t \mid s_t)\, A_t\right]
$$

$$
\mathcal{L}_{critic} = \mathbb{E}\left[(V_\phi(s_t) - \hat{V}_t)^2\right]
$$

$$
\mathcal{H}(\pi) = -\sum_a \pi(a \mid s)\log \pi(a \mid s)
$$

$$
\mathcal{L} = \mathcal{L}_{actor} + c_v \mathcal{L}_{critic} - c_e \mathcal{H}(\pi)
$$

# 1.11. Temporal-Difference learning và GAE

Temporal-Difference learning cho phép cập nhật hàm giá trị dựa trên sai số giữa giá trị ước lượng và giá trị mục tiêu một bước:

$$
\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)
$$

Trong các thuật toán actor-critic hiện đại, Generalized Advantage Estimation được dùng để ước lượng advantage ổn định hơn:

$$
A_t^{GAE(\gamma, \lambda)} = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}
$$

# 1.12. Thuật toán PPO

Proximal Policy Optimization là một trong những thuật toán học tăng cường được sử dụng phổ biến nhất hiện nay nhờ tính ổn định, hiệu quả và dễ triển khai. PPO đặc biệt phù hợp với các bài toán có action space lớn và cần huấn luyện actor-critic một cách an toàn.

Tỷ số giữa policy mới và policy cũ:

$$
\rho_t(\theta) =
\frac{\pi_\theta(a_t \mid s_t)}
{\pi_{\theta_{old}}(a_t \mid s_t)}
$$

Hàm mục tiêu clipped của PPO:

$$
\mathcal{L}^{CLIP}(\theta) =
\mathbb{E}_t
\left[
\min
\left(
\rho_t(\theta)A_t,\;
\operatorname{clip}(\rho_t(\theta), 1-\epsilon, 1+\epsilon)A_t
\right)
\right]
$$

Khi viết dưới dạng loss cần tối thiểu hóa:

$$
\mathcal{L}_{policy} = -\mathcal{L}^{CLIP}(\theta)
$$

# 1.13. Ưu điểm và hạn chế của học tăng cường

## 1.13.1. Ưu điểm

- Phù hợp với bài toán ra quyết định tuần tự.
- Có khả năng học trực tiếp theo mục tiêu tối ưu dài hạn.
- Có thể kết hợp với mạng nơ-ron để xử lý bài toán phức tạp.
- Có khả năng học chính sách có thể tái sử dụng trên nhiều episode.

## 1.13.2. Hạn chế

- Cần nhiều tài nguyên tính toán và thời gian huấn luyện.
- Nhiều thuật toán có quá trình học không ổn định.
- Rất nhạy cảm với cách thiết kế reward.
- Khó đánh giá khi chi phí tương tác với môi trường cao.
- Dễ bị overfit nếu không thiết kế thực nghiệm cẩn thận.

# 1.14. Liên hệ giữa học tăng cường và bài toán của đồ án

Trong đồ án này, bài toán macro placement được mô hình hóa thành bài toán học tăng cường như sau:

| Khái niệm RL | Ý nghĩa trong đồ án |
|---|---|
| Agent | Bộ đặt macro bằng học tăng cường |
| Environment | Môi trường placement kết hợp evaluator |
| State | Thông tin netlist, occupancy, macro hiện tại và action mask |
| Action | Chọn grid cell hợp lệ để đặt macro |
| Reward | Mức cải thiện của proxy cost hoặc reward cuối episode |
| Policy | Chiến lược đặt macro học được |

Do bài toán macro placement có tính chất quyết định tuần tự, không gian tìm kiếm rất lớn, chi phí đánh giá nghiệm cao và có nhiều ràng buộc hình học, học tăng cường là một hướng tiếp cận phù hợp về mặt lý thuyết. Đây chính là lý do phần cơ sở lý thuyết của báo cáo cần đặt nền tảng vững chắc về học tăng cường trước khi đi vào bài toán vi mạch cụ thể.

# 1.15. Kết luận chương

Chương này đã trình bày cơ sở lý thuyết nền tảng của học tăng cường, bao gồm khái niệm, mục tiêu, mô hình MDP, hàm giá trị, phương trình Bellman và các nhóm thuật toán cốt lõi như value-based, policy-based và actor-critic. Bên cạnh đó, thuật toán PPO và phương pháp ước lượng advantage bằng GAE cũng đã được giới thiệu do đây là các thành phần quan trọng trong hướng nghiên cứu của đồ án.

Từ những cơ sở lý thuyết này, các chương tiếp theo có thể trình bày cụ thể hơn về tổng quan VLSI, EDA, bài toán macro placement, dữ liệu đầu vào, môi trường học tăng cường và quá trình thực nghiệm trên stack open-source.
