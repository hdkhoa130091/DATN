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

Trong phần triển khai của đồ án, state được khai báo ở cả dạng vector đơn giản và dạng graph observation. Một ví dụ tiêu biểu là:

```python
def _get_obs(self) -> np.ndarray:
    node_idx = self._get_current_node()
    x, y = self.current_plc.get_node(node_idx)["x"], self.current_plc.get_node(node_idx)["y"]
    width, height = self.macro_dims[node_idx]

    obs = np.array(
        [
            self.current_macro_ptr / max(len(self.macro_indices), 1),
            self.previous_cost / max(self.initial_cost, 1e-9),
            self.best_cost / max(self.initial_cost, 1e-9),
            self.last_reward,
            x / max(self.canvas_width, 1e-9),
            y / max(self.canvas_height, 1e-9),
            width / max(self.canvas_width, 1e-9),
            height / max(self.canvas_height, 1e-9),
        ],
        dtype=np.float32,
    )
    return obs
```

```python
def observation_for_node(self, node_idx: int) -> dict[str, np.ndarray]:
    obs = dict(self.static_obs)
    obs["node_features"] = self._extract_node_features()
    obs["current_node"] = np.asarray(
        [self.macro_to_feature_index[node_idx]], dtype=np.int64
    )
    obs["mask"] = self.padded_mask_for_node(node_idx)
    return obs
```

Đoạn code thứ nhất cho thấy state được biểu diễn bằng 8 giá trị số thực, gồm thông tin về macro hiện tại, cost và hình học placement. Đoạn code thứ hai cho thấy trong mô hình AlphaChip-like, state được mở rộng thành một tập tensor gồm thông tin đồ thị, macro hiện tại và action mask. Cách vận hành là: sau mỗi lần environment thay đổi placement, state được dựng lại để phản ánh đúng tình trạng mới nhất của bài toán.

## 1.4.4. Action

Action là hành động mà agent có thể lựa chọn tại một trạng thái. Tập tất cả các hành động khả thi được gọi là action space. Tùy bài toán, action space có thể rời rạc hoặc liên tục.

Trong đồ án này, action là chọn một ô lưới để đặt macro hiện tại. Điều đó được khai báo và sử dụng như sau:

```python
self.action_space = gym.spaces.Discrete(self.grid_cell_count)

def _grid_cell_to_center(self, action: int) -> tuple[int, int, float, float]:
    row = action // self.grid_cols
    col = action % self.grid_cols
    x = (col + 0.5) * self.grid_width
    y = (row + 0.5) * self.grid_height
    return row, col, x, y
```

```python
dist = torch.distributions.Categorical(logits=logits)
action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
log_prob = dist.log_prob(action)
```

`action_space` cho biết toàn bộ các hành động có thể chọn là các ô trong lưới placement. Khi mạng neural suy luận, nó không trả về trực tiếp tọa độ $(x, y)$ mà trả về một chỉ số nguyên `action`. Environment sau đó biến chỉ số này thành hàng, cột và tọa độ thật trên canvas. Như vậy, action là cầu nối giữa đầu ra của policy và thao tác đặt macro cụ thể.

## 1.4.5. Reward

Reward là tín hiệu phản hồi từ môi trường, cho biết hành động vừa thực hiện tốt hay xấu theo mục tiêu tối ưu. Agent không tối ưu từng reward đơn lẻ, mà tối ưu tổng reward tích lũy trong suốt quá trình tương tác.

Reward trong code được tính từ mức cải thiện của chi phí placement hoặc từ hình phạt khi chọn action không hợp lệ:

```python
if valid:
    cost = float(self.evaluator.get_cost())
    reward = (self.previous_cost - cost) * self.reward_scale
    if reward == 0.0:
        reward = self.no_improvement_penalty
    self.previous_cost = cost
else:
    reward = self.invalid_action_penalty
```

```python
terminal_idx = len(observations) - 1
if terminal_idx >= 0 and invalid_action is None:
    rewards[terminal_idx] = (initial_cost - final_cost) * reward_scale
    dones[terminal_idx] = 1.0
```

Ở environment đơn giản, reward được sinh sau từng bước placement. Nếu cost giảm thì reward dương, nếu không có cải thiện thì bị phạt nhẹ, còn action sai thì bị phạt âm. Trong phiên bản AlphaChip-like, reward quan trọng nhất lại được gán ở cuối episode để phản ánh chất lượng placement toàn cục. Điều này cho thấy reward có thể được thiết kế linh hoạt tùy mục tiêu huấn luyện.

## 1.4.6. Policy

Policy là quy tắc mà agent sử dụng để chọn hành động dựa trên trạng thái. Đây là đối tượng trung tâm của học tăng cường, vì toàn bộ mục tiêu của việc học là tìm được một policy cho phép agent đạt hiệu quả cao nhất.

Trong mã nguồn, policy được hiện thực hóa bằng nhánh actor của mạng neural, cụ thể như sau:

```python
policy = self.policy_seed(context).view(batch, 32, seed_grid, seed_grid)
logits = self.policy_deconv(policy).flatten(start_dim=1)

mask = obs.get("mask")
if mask is not None:
    logits = logits.masked_fill(mask <= 0, -1.0e9)

dist = torch.distributions.Categorical(logits=logits)
action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
```

`context` được tạo ra từ state sau khi đi qua encoder, message passing và attention. Từ `context`, actor sinh ra `logits`, tức điểm số cho tất cả hành động có thể chọn. `mask` loại bỏ các hành động không hợp lệ, sau đó `Categorical(logits=logits)` biến các điểm số này thành phân phối xác suất. Vì vậy, policy trong code chính là cơ chế biến state thành xác suất chọn action.

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

Trong code, hàm giá trị trạng thái được hiện thực hóa bằng nhánh critic:

```python
self.value_head = MLP([context_dim, 64, 16, 1])

value = self.value_head(context).squeeze(-1)
return logits, value
```

Ở đây, `value_head` nhận `context` của trạng thái hiện tại và trả về một số thực duy nhất. Giá trị này chính là ước lượng $V(s)$, nghĩa là critic dự đoán trạng thái hiện tại tốt đến mức nào về mặt reward tương lai. Nhánh value không chọn action, nhưng nó đóng vai trò đánh giá để giúp policy học ổn định hơn.

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

Trong phần triển khai PPO, advantage được tính bằng Generalized Advantage Estimation:

```python
advantages = torch.zeros_like(rewards)
last_gae = torch.zeros((), device=self.device)
next_value = last_value
for t in reversed(range(rewards.shape[0])):
    nonterminal = 1.0 - dones[t].float()
    delta = rewards[t] + self.config.gamma * next_value * nonterminal - values[t]
    last_gae = (
        delta
        + self.config.gamma
        * self.config.gae_lambda
        * nonterminal
        * last_gae
    )
    advantages[t] = last_gae
    next_value = values[t]
```

Code đi ngược từ cuối episode về đầu episode. Ở mỗi bước, nó tính sai số TD giữa reward thực tế và giá trị mà critic đã dự đoán. Sai số này sau đó được tích lũy có chiết khấu để tạo thành `advantages`. Nếu `advantage` dương, policy sẽ được khuyến khích tăng xác suất chọn action tương ứng; nếu `advantage` âm, policy sẽ bị điều chỉnh để giảm xác suất lặp lại action đó.

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

## 1.12.1. Ví dụ triển khai PPO cho macro placement

Để làm rõ cách PPO được hiện thực hóa trong hướng nghiên cứu của đồ án, có thể xét pipeline tác tử kiểu *AlphaChip-like PPO* được xây dựng bằng PyTorch trong phần thực nghiệm. Pipeline này gồm ba khối chính:

- Bộ trích xuất đặc trưng từ dữ liệu placement và netlist.
- Mô hình actor-critic sinh hành động đặt macro và giá trị trạng thái.
- Bộ huấn luyện PPO dùng trajectory thu thập được để cập nhật tham số mạng.

Về mặt triển khai, một episode placement diễn ra theo trình tự sau:

1. Đọc netlist và placement khởi tạo bằng đối tượng `PlacementCost`.
2. Trích xuất trạng thái hiện tại thành các tensor biểu diễn đồ thị.
3. Đưa tensor qua mạng actor-critic để sinh phân phối hành động và giá trị trạng thái.
4. Chọn một ô lưới hợp lệ để đặt macro hiện tại.
5. Môi trường cập nhật placement, tính chi phí mới và sinh reward.
6. Sau khi kết thúc episode, tính `returns` và `advantages`.
7. Dùng PPO clipped loss để cập nhật actor và critic.

Một đoạn code tiêu biểu của mô hình actor-critic được viết như sau:

```python
def forward(self, obs: dict[str, torch.Tensor]) -> tuple[torch.Tensor, torch.Tensor]:
    metadata_h = self.metadata_encoder(obs["metadata"].float())
    node_h = self.node_encoder(obs["node_features"].float())

    for layer in self.gcn_layers:
        node_h = layer(
            node_h,
            obs["sparse_adj_i"],
            obs["sparse_adj_j"],
            obs["sparse_adj_weight"],
        )

    batch, _, hidden_dim = node_h.shape
    current_node = obs["current_node"].long().view(batch, 1, 1)
    current_h = node_h.gather(1, current_node.expand(-1, -1, hidden_dim)).squeeze(1)
    attended_h = self._attention(current_h, node_h)

    edge_mean = node_h.mean(dim=1)
    edge_var = node_h.var(dim=1, unbiased=False)
    edge_max = node_h.max(dim=1).values
    context = torch.cat(
        [metadata_h, edge_mean, edge_var, edge_max, attended_h, current_h],
        dim=-1,
    )

    policy = self.policy_seed(context).view(batch, 32, seed_grid, seed_grid)
    logits = self.policy_deconv(policy).flatten(start_dim=1)
    value = self.value_head(context).squeeze(-1)

    mask = obs.get("mask")
    if mask is not None:
        logits = logits.masked_fill(mask <= 0, -1.0e9)

    return logits, value
```

Đoạn code trên cho thấy rõ hai đầu ra quan trọng của mô hình:

- `logits`: điểm số cho tất cả vị trí có thể đặt macro trên lưới.
- `value`: giá trị trạng thái do critic ước lượng để phục vụ PPO.

## 1.12.2. Luồng tensor dữ liệu trong mô hình

Trong bài toán macro placement, trạng thái đầu vào không phải là một vector đơn giản mà là một tập tensor biểu diễn netlist, vị trí macro và các ràng buộc đặt chỗ. Sau khi trích xuất đặc trưng, một mẫu dữ liệu đầu vào thường gồm:

- `metadata`: vector mô tả thống kê toàn cục của netlist và canvas.
- `node_features`: ma trận đặc trưng của macro và port cluster.
- `sparse_adj_i`, `sparse_adj_j`, `sparse_adj_weight`: biểu diễn cạnh thưa của đồ thị kết nối.
- `current_node`: chỉ số macro đang cần được đặt ở bước hiện tại.
- `mask`: mặt nạ hành động chỉ ra những ô lưới hợp lệ.

Nếu xét một batch kích thước $B$, số node tối đa là $N$, số cạnh tối đa là $E$ và lưới placement được đệm về kích thước $G \times G$, các tensor có thể được biểu diễn như sau:

- `metadata`: $[B, 12]$
- `node_features`: $[B, N, 8]$
- `sparse_adj_i`: $[B, E]$
- `sparse_adj_j`: $[B, E]$
- `sparse_adj_weight`: $[B, E]$
- `current_node`: $[B, 1]$
- `mask`: $[B, G^2]$

Luồng truyền của tensor trong mô hình diễn ra theo các bước:

1. `metadata` đi qua `metadata_encoder` để tạo ra embedding toàn cục $[B, H]$.
2. `node_features` đi qua `node_encoder` để tạo embedding node $[B, N, H]$.
3. Các cạnh `sparse_adj_i`, `sparse_adj_j`, `sparse_adj_weight` được dùng trong các lớp message passing kiểu GCN để cập nhật embedding của từng node.
4. `current_node` được dùng như một chỉ số để trích ra embedding của macro hiện tại từ tensor `node_h`.
5. Cơ chế attention sử dụng embedding của macro hiện tại để tổng hợp thông tin từ toàn bộ đồ thị.
6. Các vector ngữ cảnh như `metadata_h`, `edge_mean`, `edge_var`, `edge_max`, `attended_h` và `current_h` được nối lại thành một tensor ngữ cảnh chung.
7. Tensor ngữ cảnh này được đưa vào hai nhánh:
   - Nhánh actor sinh `logits` cho tất cả ô lưới.
   - Nhánh critic sinh `value` cho trạng thái hiện tại.
8. `mask` được áp vào `logits` để loại bỏ các hành động không hợp lệ bằng cách gán giá trị rất âm, nhờ đó phân phối xác suất gần như bằng 0 tại các vị trí bị cấm.

Ý nghĩa trực quan của flow trên là: mô hình trước hết hiểu cấu trúc kết nối của netlist dưới dạng đồ thị, sau đó tập trung vào macro đang được xét ở bước hiện tại, rồi mới quyết định nên đặt macro đó vào ô nào trên lưới.

## 1.12.3. Luồng dữ liệu trong một episode huấn luyện

Trong quá trình huấn luyện, dữ liệu không chỉ đi theo chiều thuận từ đầu vào đến đầu ra, mà còn quay ngược trở lại qua hàm loss để cập nhật tham số. Luồng này có thể mô tả như sau:

1. Môi trường sinh observation tại bước $t$.
2. Observation được biến đổi thành tensor và đưa qua actor-critic.
3. Actor sinh phân phối hành động, từ đó lấy ra action $a_t$ và log-probability tương ứng.
4. Critic sinh giá trị trạng thái $V(s_t)$.
5. Action được áp dụng vào môi trường placement để nhận trạng thái mới và reward.
6. Sau khi hoàn thành episode, toàn bộ chuỗi $(s_t, a_t, r_t)$ được gom lại thành rollout batch.
7. Từ rollout batch, thuật toán tính:

$$
\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)
$$

và

$$
A_t^{GAE(\gamma,\lambda)} = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}
$$

8. Actor được cập nhật bằng tỷ số giữa policy mới và policy cũ:

$$
\rho_t(\theta) =
\frac{\pi_\theta(a_t \mid s_t)}
{\pi_{\theta_{old}}(a_t \mid s_t)}
$$

9. Hàm loss của PPO sử dụng cơ chế clipping để tránh cập nhật quá mạnh:

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

10. Critic được cập nhật bằng sai số bình phương giữa `returns` và `value`.

Như vậy, có thể hình dung toàn bộ vòng lặp học như sau:

`PlacementCost -> Feature Extractor -> Tensor Observation -> Actor-Critic -> Action -> Placement Environment -> Reward -> GAE -> PPO Loss -> Backpropagation`

Điểm quan trọng của kiến trúc này là dữ liệu hình học và dữ liệu kết nối của netlist không bị tách rời. Thay vào đó, chúng được ghép lại trong cùng một graph-based observation, cho phép tác tử học được mối liên hệ giữa vị trí placement của macro và chi phí toàn cục của thiết kế.

## 1.12.4. Đối chiếu các khái niệm RL với thành phần trong code

Để tránh việc các khái niệm như *state*, *action*, *policy* hay *value* chỉ dừng ở mức lý thuyết, phần này đối chiếu trực tiếp từng khái niệm với các biến, hàm và cấu trúc dữ liệu xuất hiện trong mã nguồn của tác tử PPO cho macro placement.

### State

Trong học tăng cường, *state* là biểu diễn của tình trạng hiện tại của môi trường tại thời điểm tác tử cần ra quyết định. Trong mã nguồn của đồ án, state xuất hiện ở hai mức:

- Mức đơn giản trong environment dạng vector 8 chiều.
- Mức đầy đủ trong tác tử kiểu AlphaChip dưới dạng tập tensor biểu diễn đồ thị.

Ở environment đơn giản, hàm `_get_obs()` tạo ra state dưới dạng:

- chỉ số macro hiện tại đang được xử lý,
- chi phí placement hiện tại đã chuẩn hóa,
- chi phí tốt nhất đã biết,
- reward của bước trước,
- tọa độ hiện tại của macro,
- kích thước của macro.

Biểu diễn này phù hợp cho các thử nghiệm RL cơ bản, nơi state chỉ cần chứa một số đặc trưng tổng quát.

Trong pipeline AlphaChip-like, state được xây dựng bởi `observation_for_node()` và gồm các thành phần:

- `metadata`: đặc trưng toàn cục của netlist và canvas,
- `node_features`: đặc trưng theo node cho macro và port cluster,
- `sparse_adj_i`, `sparse_adj_j`, `sparse_adj_weight`: các cạnh của đồ thị kết nối,
- `current_node`: macro đang cần đặt ở bước hiện tại,
- `mask`: mặt nạ hành động hợp lệ.

Như vậy, trong triển khai nâng cao của đồ án, *state* không còn là một vector ngắn mà là một graph observation, cho phép mô hình khai thác đồng thời thông tin hình học và thông tin kết nối.

Đoạn code khai báo và xây dựng state được thể hiện như sau:

```python
def _get_obs(self) -> np.ndarray:
    node_idx = self._get_current_node()
    x, y = self.current_plc.get_node(node_idx)["x"], self.current_plc.get_node(node_idx)["y"]
    width, height = self.macro_dims[node_idx]

    obs = np.array(
        [
            self.current_macro_ptr / max(len(self.macro_indices), 1),
            self.previous_cost / max(self.initial_cost, 1e-9),
            self.best_cost / max(self.initial_cost, 1e-9),
            self.last_reward,
            x / max(self.canvas_width, 1e-9),
            y / max(self.canvas_height, 1e-9),
            width / max(self.canvas_width, 1e-9),
            height / max(self.canvas_height, 1e-9),
        ],
        dtype=np.float32,
    )
    return obs
```

```python
def observation_for_node(self, node_idx: int) -> dict[str, np.ndarray]:
    obs = dict(self.static_obs)
    obs["node_features"] = self._extract_node_features()
    obs["current_node"] = np.asarray(
        [self.macro_to_feature_index[node_idx]], dtype=np.int64
    )
    obs["mask"] = self.padded_mask_for_node(node_idx)
    return obs
```

Trong đoạn code thứ nhất, state được khai báo dưới dạng vector 8 chiều để environment đơn giản có thể trả về ngay cho agent. Trong đoạn code thứ hai, state được mở rộng thành một tập tensor có cấu trúc đồ thị. Cách vận hành là: sau mỗi bước placement, thông tin vị trí macro, cost và mask được cập nhật lại, từ đó tạo ra state mới phản ánh đúng tình trạng hiện tại của môi trường.

### Action

*Action* là quyết định mà agent thực hiện khi quan sát một state. Trong bài toán này, action là lựa chọn một ô lưới để đặt macro hiện tại.

Trong environment, không gian hành động được định nghĩa là:

$$
\texttt{Discrete}(\texttt{grid\_cell\_count})
$$

Điều này có nghĩa là mỗi action là một số nguyên biểu diễn một vị trí trên lưới placement. Từ chỉ số này, code chuyển đổi sang hàng, cột và tọa độ tâm của ô lưới tương ứng.

Trong tác tử AlphaChip-like, action được sinh từ phân phối rời rạc `Categorical(logits=logits)`. Biến `logits` là điểm số cho toàn bộ vị trí đặt có thể xảy ra, còn action là kết quả lấy mẫu hoặc lấy `argmax` từ phân phối đó.

Do lưới trong mô hình được đệm về kích thước chuẩn, action sau khi sinh ra còn cần được ánh xạ từ chỉ số trong lưới đệm sang ô lưới thật của bài toán placement. Vì vậy, action trong code có hai mức:

- `padded_action`: chỉ số trên lưới đệm mà mạng neural dự đoán,
- `real_action`: chỉ số ô lưới thật được dùng để gọi hàm `place_node()`.

Đoạn code thể hiện nơi action được khai báo và sử dụng là:

```python
self.action_space = gym.spaces.Discrete(self.grid_cell_count)

def _grid_cell_to_center(self, action: int) -> tuple[int, int, float, float]:
    row = action // self.grid_cols
    col = action % self.grid_cols
    x = (col + 0.5) * self.grid_width
    y = (row + 0.5) * self.grid_height
    return row, col, x, y
```

```python
dist = torch.distributions.Categorical(logits=logits)
action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
log_prob = dist.log_prob(action)
return action, log_prob, value
```

Action trước hết được khai báo như một phần tử trong không gian rời rạc của lưới placement. Sau đó, policy của mạng sinh ra một action dưới dạng chỉ số nguyên. Environment sẽ dùng chỉ số này để suy ra hàng, cột và tọa độ thực trên canvas. Như vậy, về mặt vận hành, action là cầu nối giữa đầu ra của mạng neural và thao tác đặt macro cụ thể trong môi trường.

### Reward

*Reward* là tín hiệu phản hồi của môi trường sau khi tác tử thực hiện action. Trong bài toán macro placement, reward phản ánh placement vừa thực hiện có giúp cải thiện chi phí hay không.

Trong environment đơn giản, reward được tính từ chênh lệch chi phí trước và sau hành động:

$$
r_t = (\text{cost}_{t-1} - \text{cost}_t)\cdot \text{reward\_scale}
$$

Nếu action không làm placement tốt hơn, code có thể gán một giá trị phạt nhỏ. Nếu action không hợp lệ, code gán một mức phạt âm rõ ràng hơn. Điều này giúp agent học tránh các vị trí không thể đặt hoặc không mang lại cải thiện.

Trong bản huấn luyện AlphaChip-like, reward chủ yếu được gán ở cuối episode. Cụ thể, sau khi đặt xong chuỗi macro, reward cuối cùng được tính từ mức cải thiện giữa chi phí ban đầu và chi phí cuối:

$$
r_{\text{terminal}} = (\text{initial\_cost} - \text{final\_cost})\cdot \text{reward\_scale}
$$

Nếu trong quá trình placement có action không hợp lệ, episode bị dừng sớm và nhận reward âm. Thiết kế reward như vậy khiến bài toán thiên về tối ưu chất lượng placement toàn cục thay vì chỉ tối ưu từng bước cục bộ.

Đoạn code tính reward trong environment và trong PPO trainer như sau:

```python
if valid:
    cost = float(self.evaluator.get_cost())
    reward = (self.previous_cost - cost) * self.reward_scale
    if reward == 0.0:
        reward = self.no_improvement_penalty
    self.previous_cost = cost
else:
    reward = self.invalid_action_penalty
```

```python
terminal_idx = len(observations) - 1
if terminal_idx >= 0 and invalid_action is None:
    rewards[terminal_idx] = (initial_cost - final_cost) * reward_scale
    dones[terminal_idx] = 1.0
```

Đoạn code đầu cho thấy reward được tạo ngay sau mỗi bước tương tác với environment. Nếu placement làm giảm cost thì reward dương, nếu không hợp lệ thì bị phạt. Đoạn code thứ hai cho thấy trong bản AlphaChip-like, reward quan trọng nhất lại được dồn về cuối episode để phản ánh chất lượng placement tổng thể. Vì vậy, cùng là reward nhưng chiến lược thiết kế reward có thể thay đổi theo cách huấn luyện.

### Policy

*Policy* là quy tắc chọn action dựa trên state, tức là hàm xác suất $\pi(a \mid s)$. Trong code, policy không được lưu dưới tên `policy` như một bảng hay một hàm tách biệt, mà được hiện thực hóa bằng mạng actor trong mô hình actor-critic.

Cụ thể, nhánh actor nhận state và sinh ra tensor `logits`. Từ `logits`, code tạo phân phối:

$$
\pi_\theta(a \mid s) = \text{Categorical}(\text{logits})
$$

Do đó:

- `logits` là biểu diễn trước softmax của policy,
- `dist = Categorical(logits=logits)` là policy dưới dạng phân phối xác suất,
- `action = dist.sample()` hoặc `argmax(logits)` là hành động được chọn theo policy.

Nói cách khác, *policy* trong code chính là toàn bộ phần mạng neural chịu trách nhiệm biến state thành xác suất chọn các vị trí đặt macro.

Ô code thể hiện policy trong mô hình như sau:

```python
policy = self.policy_seed(context).view(batch, 32, seed_grid, seed_grid)
logits = self.policy_deconv(policy).flatten(start_dim=1)

mask = obs.get("mask")
if mask is not None:
    logits = logits.masked_fill(mask <= 0, -1.0e9)

dist = torch.distributions.Categorical(logits=logits)
action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
```

Cách vận hành của policy là: từ `context` trích xuất từ state, nhánh actor sinh ra `logits` cho toàn bộ ô lưới. Sau đó `mask` loại bỏ các action không hợp lệ. Cuối cùng `Categorical(logits=logits)` biến các điểm số thành phân phối xác suất để tác tử chọn action. Như vậy, policy không chỉ là một công thức xác suất mà là cả chuỗi xử lý từ state sang `logits`, rồi từ `logits` sang hành động.

### Action Mask

Trong nhiều bài toán RL thông thường, policy có thể chọn bất kỳ action nào trong action space. Tuy nhiên, trong macro placement, nhiều ô lưới là không hợp lệ do:

- macro vượt biên canvas,
- macro chồng lấn lên phần tử đã đặt,
- macro vi phạm ràng buộc hình học.

Vì vậy, code sử dụng `mask` để đánh dấu action hợp lệ. Khi `mask` được áp lên `logits`, các action không hợp lệ bị gán giá trị rất âm. Sau bước softmax ngầm trong phân phối `Categorical`, xác suất của các action này gần như bằng 0.

Điểm này rất quan trọng vì nó giúp tác tử không lãng phí quá trình học vào các hành động chắc chắn sai về mặt hình học.

Đoạn code xây dựng và áp dụng action mask là:

```python
def action_masks(self) -> np.ndarray:
    node_idx = self._get_current_node()
    mask = np.zeros(self.action_space.n, dtype=bool)
    for action in range(self.action_space.n):
        mask[action] = self._is_valid_placement(node_idx, action)
    if not mask.any():
        mask[:] = True
    return mask
```

```python
mask = obs.get("mask")
if mask is not None:
    logits = logits.masked_fill(mask <= 0, -1.0e9)
```

Đầu tiên environment hoặc feature extractor duyệt các vị trí có thể đặt để tạo `mask`. Sau đó khi model sinh `logits`, các vị trí bị cấm sẽ bị gán giá trị rất âm. Nhờ đó, phân phối action gần như loại bỏ hoàn toàn các lựa chọn không hợp lệ trước khi agent thực sự lấy mẫu hành động.

### Value

*Value* là giá trị trạng thái do critic ước lượng, thường ký hiệu là $V(s)$. Trong code, `value` được sinh ra bởi nhánh critic của mô hình actor-critic:

$$
V_\phi(s) = \text{value\_head}(\text{context})
$$

Ý nghĩa của `value` là ước lượng xem state hiện tại hứa hẹn mang lại tổng reward tương lai lớn đến mức nào nếu tiếp tục hành động theo policy hiện thời. Khác với actor, critic không trực tiếp chọn action mà chỉ đóng vai trò đánh giá state để ổn định quá trình huấn luyện.

Đoạn code khai báo và sinh `value` là:

```python
self.value_head = MLP([context_dim, 64, 16, 1])

value = self.value_head(context).squeeze(-1)
return logits, value
```

Ở đây, `value_head` là nhánh critic của mạng. Sau khi actor và critic cùng dùng chung `context`, critic ánh xạ `context` thành một số thực duy nhất. Số này chính là dự đoán $V(s)$, tức mức tốt của trạng thái hiện tại. Trong quá trình vận hành, `value` được dùng về sau để tính TD error, advantage và value loss.

### Return

*Return* là tổng reward mục tiêu mà critic cần học để dự đoán. Trong triển khai PPO của đồ án, `returns` được tính từ `advantages` cộng với `values`:

$$
\texttt{returns} = \texttt{advantages} + \texttt{values}
$$

Sau đó, critic được huấn luyện bằng cách giảm sai số giữa `returns` và `value` do mạng dự đoán. Vì vậy, return đóng vai trò như nhãn huấn luyện cho critic trong từng rollout.

Đoạn code thể hiện `return` là:

```python
returns = advantages + values
return returns.detach(), advantages.detach()
```

```python
value_loss = torch.square(batch.returns - values).mean()
```

Code trên cho thấy `return` không được khai báo như một phần cố định của environment, mà được tính sau khi thu thập rollout. Sau đó `returns` được dùng như mục tiêu để huấn luyện critic. Nói cách khác, `return` là tín hiệu học ngược trở lại vào nhánh value của mạng.

### Advantage

*Advantage* cho biết action vừa chọn tốt hơn hay kém hơn mức kỳ vọng tại state đó. Nếu advantage dương, action tốt hơn dự đoán trung bình của critic. Nếu advantage âm, action tệ hơn dự đoán.

Trong code, advantage được tính bằng phương pháp GAE. Đầu tiên tính sai số TD:

$$
\delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)
$$

Sau đó tích lũy có chiết khấu để thu được:

$$
A_t^{GAE(\gamma,\lambda)} = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}
$$

Biến `advantages` này là thành phần rất quan trọng trong PPO vì nó quyết định hướng cập nhật policy. Nếu một action có `advantage` lớn, xác suất chọn action đó sẽ được tăng lên. Nếu `advantage` âm, policy sẽ bị điều chỉnh để giảm xác suất lặp lại action đó.

Đoạn code tính `advantage` bằng GAE là:

```python
advantages = torch.zeros_like(rewards)
last_gae = torch.zeros((), device=self.device)
next_value = last_value
for t in reversed(range(rewards.shape[0])):
    nonterminal = 1.0 - dones[t].float()
    delta = rewards[t] + self.config.gamma * next_value * nonterminal - values[t]
    last_gae = (
        delta
        + self.config.gamma
        * self.config.gae_lambda
        * nonterminal
        * last_gae
    )
    advantages[t] = last_gae
    next_value = values[t]
```

Về cách vận hành, code đi ngược từ cuối episode về đầu episode. Ở mỗi bước, nó tính sai số giữa reward thực nhận cộng giá trị tương lai với giá trị hiện tại mà critic dự đoán. Sai số này được tích lũy có chiết khấu để tạo ra `advantages`. Chính `advantages` sẽ nói cho policy biết hành động nào nên được tăng xác suất và hành động nào nên bị giảm xác suất trong lần cập nhật tiếp theo.

### Log-probability và policy cũ

Một chi tiết quan trọng trong PPO là cần so sánh policy hiện tại với policy đã dùng khi thu thập dữ liệu. Trong code, điều này được thực hiện thông qua:

- `old_log_probs`: log-xác suất của action tại thời điểm thu thập rollout,
- `log_probs`: log-xác suất mới khi chạy lại policy hiện tại trên cùng batch dữ liệu.

Từ hai đại lượng này, code tính:

$$
\rho_t(\theta) = \exp\left(\log \pi_\theta(a_t \mid s_t) - \log \pi_{\theta_{old}}(a_t \mid s_t)\right)
$$

Đây là tỷ số trung tâm của PPO, quyết định mức độ thay đổi policy có còn nằm trong vùng an toàn hay không.

Đoạn code tương ứng là:

```python
logits, values = self.model(batch.obs)
dist = torch.distributions.Categorical(logits=logits)
log_probs = dist.log_prob(batch.actions)

ratio = torch.exp(log_probs - batch.old_log_probs)
unclipped = ratio * batch.advantages
clipped = torch.clamp(
    ratio,
    1.0 - self.config.clip_range,
    1.0 + self.config.clip_range,
) * batch.advantages
policy_loss = -torch.min(unclipped, clipped).mean()
```

Đầu tiên policy hiện tại được chạy lại trên cùng batch dữ liệu để tính `log_probs` mới. Sau đó code so sánh với `old_log_probs` đã lưu khi thu thập rollout để tạo ra `ratio`. Nếu `ratio` thay đổi quá lớn, toán hạng `clipped` sẽ khống chế mức cập nhật. Đây là cơ chế cốt lõi giúp PPO ổn định hơn so với việc cập nhật policy quá mạnh sau mỗi rollout.

### Tổng kết vai trò của các thành phần

Nếu đối chiếu ngắn gọn giữa lý thuyết RL và triển khai thực tế trong đồ án, có thể tóm tắt như sau:

- `state`: observation hoặc graph observation của placement hiện tại.
- `action`: ô lưới được chọn để đặt macro.
- `reward`: mức cải thiện hoặc mức phạt sau khi placement.
- `policy`: phân phối xác suất sinh từ `logits` của actor.
- `value`: giá trị trạng thái do critic ước lượng.
- `return`: mục tiêu học của critic.
- `advantage`: mức tốt hơn hoặc kém hơn kỳ vọng của action đã chọn.

Việc đối chiếu này cho thấy các khái niệm RL trong chương lý thuyết hoàn toàn không tách rời phần thực nghiệm. Ngược lại, chúng xuất hiện trực tiếp dưới dạng biến, tensor và hàm cập nhật trong mã nguồn, tạo nên một pipeline nhất quán từ mô hình toán học đến chương trình huấn luyện thực tế.

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
