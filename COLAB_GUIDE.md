# Hướng dẫn chạy Circuit Training trên Google Colab

## Ưu điểm của Colab so với Windows local:

| Tiêu chí | Windows Local | Google Colab |
|----------|--------------|--------------|
| **OS** | Windows (port) | Ubuntu Linux (gốc) |
| **GPU** | RTX 3060 (tốn phí net) | Tesla T4/K80 (free) |
| **Setup** | Phức tạp (đã xong) | Đơn giản |
| **Thời gian** | Lâu (build dependencies) | Nhanh (15 phút) |
| **Lưu trữ** | Local (mất khi restart) | Google Drive (vĩnh viễn) |
| **DREAMPlace** | Khó build | Build dễ dàng |

## Cách sử dụng:

### Bước 1: Upload notebook lên Colab

1. Truy cập: https://colab.research.google.com
2. File → Upload notebook → Chọn `circuit_training_colab.ipynb`

### Bước 2: Cấu hình GPU

1. Runtime → Change runtime type
2. Hardware accelerator: **GPU** (T4 hoặc A100 nếu có)
3. Click Save

### Bước 3: Chạy từng cell

Click vào từng cell và nhấn ▶️ hoặc `Ctrl+Enter`

**Thứ tự:**
1. ✅ Kiểm tra GPU
2. ✅ Mount Google Drive
3. ✅ Clone repos (5-10 phút)
4. ✅ Cài dependencies (5 phút)
5. ✅ Build DREAMPlace (15-20 phút)
6. ✅ Test import
7. ✅ Training!

### Bước 4: Lưu kết quả

Kết quả tự động lưu vào Google Drive tại:
```
MyDrive/circuit_training_project/logs/
```

## Quan trọng - Tránh mất kết nối:

Colab disconnect sau 90 phút idle hoặc 12 giờ liên tục.

**Cách giữ session:**
- Mở Developer Console (F12)
- Vào Console tab
- Dán code này:
```javascript
function KeepAlive() {
    setInterval(() => {
        document.querySelector("colab-toolbar-button").click();
        console.log("Kept alive at", new Date());
    }, 60000);
}
KeepAlive();
```

## So sánh thời gian training:

| Benchmark | Windows (RTX 3060) | Colab (T4) |
|-----------|-------------------|------------|
| toy_macro_stdcell (10 macros) | 10 phút | 15 phút |
| ariane133 (133 macros) | 2-3 giờ | 3-4 giờ |
| mempool (200+ macros) | 6-8 giờ | 8-10 giờ |

## Lưu ý:

1. **Đừng đóng trình duyệt** khi đang training
2. **Save checkpoint thường xuyên** (đã tự động trong code)
3. **Dùng toy benchmark trước** để test flow
4. **Premium Colab** ($9.99/tháng): GPU mạnh hơn, session dài hơn

## File cần upload từ máy hiện tại:

- ✅ `circuit_training_colab.ipynb` - Notebook chính
- 📁 `MacroPlacement/Testcases/` (nếu muốn dùng benchmark lớn)

## Kết luận:

**Colab là lựa chọn tốt nhất** vì:
- Linux gốc (Circuit Training chạy tốt nhất)
- Không cần cài đặt phức tạp
- Lưu trữ vĩnh viễn trên Drive
- Free GPU

**Hạn chế:**
- Phải giữ tab mở
- Giới hạn 12 giờ/session
- Cần internet ổn định

---

**Tiếp theo:** Mở file `circuit_training_colab.ipynb` và upload lên https://colab.research.google.com
