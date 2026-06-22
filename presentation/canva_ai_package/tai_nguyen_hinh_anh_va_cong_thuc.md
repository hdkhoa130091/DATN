# Tài nguyên hình ảnh và công thức cho Canva AI

## 1. Cách dùng

Khi đưa lên Canva AI, nên upload cùng lúc:

- `canva_prompt_vi.txt`
- `noi_dung_ly_thuyet_va_quy_trinh_vi.md`
- toàn bộ ảnh trong thư mục `assets/`

Canva AI có thể dùng:

- prompt để hiểu mục tiêu trình bày,
- file markdown để lấy nội dung lý thuyết,
- ảnh để dựng slide có tính trực quan hơn.

---

## 2. Danh mục ảnh đã chọn

Tất cả ảnh này đã được copy sẵn vào:

```text
presentation/canva_ai_package/assets/
```

### 2.1 Ảnh minh họa bài toán macro placement

- `macro_example.png`
  - minh họa macro placement ở mức khái niệm

- `net_model.png`
  - minh họa graph / net model dùng trong RL

- `Gridding Algorithm.png`
  - minh họa cách chia canvas thành grid

### 2.2 Ảnh luồng đánh giá / flow

- `EvaluationFlows.png`
  - minh họa các luồng đánh giá placement

- `ORFS_Flow.svg`
  - hình flow OpenROAD Flow Scripts

- `rtl2gds.svg`
  - minh họa flow RTL-to-GDS

### 2.3 Ảnh benchmark Ariane133

- `CT_Placement.png`
  - baseline placement theo Circuit Training

- `CT_Routing.png`
  - routing tương ứng của baseline CT

- `Human_Gridded_Placement.png`
  - baseline macro placement thủ công trên lưới

- `Human_Expert_Placement.png`
  - baseline macro placement do chuyên gia cung cấp

- `Innovus_Flow2_Placement.png`
  - placement từ flow Cadence / baseline trước RL

- `Ariane133_ORFS.png`
  - kết quả placement bằng OpenROAD / ORFS

---

## 3. Gợi ý ghép ảnh theo slide

### Slide bài toán

Dùng:

- `macro_example.png`
- `net_model.png`

### Slide translator / format change

Dùng:

- `Gridding Algorithm.png`
- `EvaluationFlows.png`

### Slide benchmark và baseline

Dùng:

- `CT_Placement.png`
- `Human_Gridded_Placement.png`
- `Human_Expert_Placement.png`
- `Innovus_Flow2_Placement.png`
- `Ariane133_ORFS.png`

### Slide EDA tổng quát

Dùng:

- `rtl2gds.svg`
- `ORFS_Flow.svg`

---

## 4. Công thức nên đưa vào slide

Để tránh lỗi render toán, nên dùng bản plain text dưới đây khi đưa vào Canva AI.

### 4.1 Policy ratio

```text
r_t(theta) = pi_theta(a_t | s_t) / pi_theta_old(a_t | s_t)
```

### 4.2 PPO clipped objective

```text
L_CLIP(theta) =
E_t[
  min(
    r_t(theta) * A_hat_t,
    clip(r_t(theta), 1 - epsilon, 1 + epsilon) * A_hat_t
  )
]
```

### 4.3 Value loss

```text
L_VF(theta) = E_t[(V_theta(s_t) - R_t)^2]
```

### 4.4 Entropy bonus

```text
L_ENT(theta) = E_t[ H(pi_theta(. | s_t)) ]
```

### 4.5 Tổng objective

```text
L(theta) = L_CLIP(theta) - c1 * L_VF(theta) + c2 * L_ENT(theta)
```

### 4.6 TD error và GAE

```text
delta_t = r_t + gamma * V(s_{t+1}) - V(s_t)
```

```text
A_hat_t = delta_t
        + (gamma * lambda) * delta_{t+1}
        + (gamma * lambda)^2 * delta_{t+2}
        + ...
```

---

## 5. Diễn giải ngắn để đặt cạnh công thức

### Episode

- một lần đặt xong một lượt macro

### Rollout episodes

- số episode dùng để thu dữ liệu trước khi PPO cập nhật

### Observation

- trạng thái placement hiện tại:
  - metadata
  - graph connectivity
  - node features
  - current macro
  - mask

### Action

- chọn một ô lưới để đặt macro

### Reward / cost

- đánh giá placement bằng wirelength, density, congestion proxy

---

## 6. Chuỗi từ khóa nên dùng trong slide

Các cụm nên xuất hiện trên sơ đồ:

- RTL / Constraints
- Synthesis
- DEF / LEF / Metadata
- Format Change / Translator
- netlist.pb.txt
- initial.plc
- legalized.plc
- PlacementCost Environment
- Observation / State
- Actor-Critic Policy
- Macro Placement Action
- Reward / Proxy Cost
- PPO Update
- final.plc
- OpenROAD Validation

---

## 7. Thông điệp chính nên nhấn mạnh

1. RL không thay thế toàn bộ EDA.
2. RL nằm ở phần macro placement.
3. Dữ liệu phải được chuyển đổi từ flow EDA sang format RL.
4. Kết quả RL phải quay lại flow EDA để kiểm chứng.
5. Giá trị của dự án là làm thông toàn bộ pipeline AI + EDA.
