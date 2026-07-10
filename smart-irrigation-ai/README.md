# Hệ thống tưới cây thông minh — ESP32 + ThingSpeak
## Module Phân tích dữ liệu & AI

Đồ án xây dựng module Python phân tích dữ liệu cảm biến (nhiệt độ, độ ẩm đất, độ ẩm
không khí, ánh sáng) thu thập từ ThingSpeak, kết hợp AI dự báo đơn giản (Moving
Average + Linear Regression) và thuật toán quyết định điều khiển máy bơm tưới cây.

---

## 1. Cấu trúc thư mục

```
smart-irrigation-ai/
├── data/                        # Dữ liệu thô, dữ liệu đã làm sạch, dữ liệu mô phỏng
├── notebook/
│   └── smart_irrigation_analysis.ipynb   # Notebook tổng hợp toàn bộ pipeline
├── src/
│   ├── api.py                  # Đọc dữ liệu từ ThingSpeak API
│   ├── preprocess.py           # Làm sạch dữ liệu + sinh dữ liệu mô phỏng
│   ├── analysis.py             # Thống kê mô tả + ma trận tương quan
│   ├── visualization.py        # Vẽ 7 biểu đồ phân tích
│   ├── prediction.py           # AI dự báo: Moving Average + Linear Regression
│   └── irrigation_logic.py     # Thuật toán quyết định bật/tắt bơm
├── report/
│   ├── BaoCao.docx              # Báo cáo đồ án đầy đủ (bản Word)
│   ├── BaoCao.md                # Báo cáo đồ án đầy đủ (bản Markdown, có sơ đồ Mermaid nhúng)
│   ├── ThuyetTrinh.md           # Kịch bản thuyết trình ~3 phút
│   └── diagrams/                # Sơ đồ Mermaid (.mmd)
├── images/                      # Biểu đồ xuất ra (PNG)
└── README.md
```

---

## 2. Cài đặt

Yêu cầu: Python ≥ 3.9

```bash
pip install requests pandas numpy matplotlib scikit-learn scipy
```

(Google Colab đã cài sẵn hầu hết các thư viện trên.)

---

## 3. Cách lấy / thay ThingSpeak API Key

1. Đăng nhập [ThingSpeak](https://thingspeak.com), mở Channel chứa dữ liệu cảm biến ESP32.
2. Vào tab **API Keys**, sao chép:
   - **Channel ID** (hiển thị ở đầu trang Channel).
   - **Read API Key** (chỉ cần thiết nếu Channel ở chế độ *Private*).
3. Mở file `src/api.py` (hoặc ô cấu hình trong notebook) và thay:

```python
CHANNEL_ID = "YOUR_CHANNEL_ID"
READ_API_KEY = "YOUR_READ_API_KEY"
```

4. Nếu chưa deploy phần cứng ESP32 / chưa có dữ liệu thật, đặt `USE_REAL_DATA = False`
   trong notebook — hệ thống sẽ tự động dùng dữ liệu mô phỏng từ
   `preprocess.generate_simulated_data()` (500 dòng, mô phỏng chu kỳ ngày/đêm thực tế).

---

## 4. Chạy trên Google Colab

1. Nén thư mục `smart-irrigation-ai/` (hoặc chỉ `src/` + `data/`) và upload lên Colab,
   hoặc mount Google Drive rồi copy thư mục vào đó.
2. Mở file `notebook/smart_irrigation_analysis.ipynb` bằng Colab
   (File → Upload notebook, hoặc mở trực tiếp từ Drive).
3. Đảm bảo cấu trúc thư mục trên Colab như sau (notebook mặc định tìm `../src`):

```
/content/smart-irrigation-ai/
├── src/
├── data/
├── images/
└── notebook/smart_irrigation_analysis.ipynb
```

4. Chạy lần lượt từng ô (Runtime → Run all).

---

## 5. Chạy trên VS Code (cục bộ)

1. Cài Python extension + Jupyter extension cho VS Code.
2. Mở thư mục `smart-irrigation-ai/` bằng VS Code.
3. Mở terminal, cài thư viện:

```bash
pip install -r requirements.txt   # hoặc pip install requests pandas numpy matplotlib scikit-learn scipy
```

4. Chạy từng module độc lập để kiểm tra, ví dụ:

```bash
cd src
python preprocess.py       # sinh dữ liệu mô phỏng -> data/simulated_data.csv
python analysis.py         # in bảng thống kê
python visualization.py    # xuất 7 biểu đồ vào images/
python prediction.py       # chạy AI dự báo, xuất biểu đồ dự báo
python irrigation_logic.py # test nhanh thuật toán quyết định
```

5. Hoặc mở `notebook/smart_irrigation_analysis.ipynb` trực tiếp trong VS Code
   (chọn kernel Python phù hợp) để chạy toàn bộ pipeline theo từng ô.

---

## 6. Quy tắc điều khiển bơm (tóm tắt)

| Điều kiện | Hành động |
|---|---|
| Soil Moisture < 40% | Bật bơm (PUMP ON) |
| Soil Moisture > 60% | Tắt bơm (PUMP OFF) |
| 40% ≤ Soil Moisture ≤ 60% | Giữ nguyên trạng thái |
| Moving Average giảm liên tục | Cảnh báo "sắp khô" |

Chi tiết thuật toán và sơ đồ logic xem tại `report/diagrams/irrigation_decision_logic.mmd`
và mô-đun `src/irrigation_logic.py`.

---

## 7. Tài liệu đi kèm

- `report/BaoCao.docx` — Báo cáo đồ án đầy đủ theo chuẩn đại học (bản Word).
- `report/BaoCao.md` — Cùng nội dung báo cáo ở định dạng Markdown, có nhúng sẵn sơ đồ Mermaid (hiển thị trực tiếp trên GitHub/VS Code).
- `report/ThuyetTrinh.md` — Kịch bản thuyết trình khoảng 3 phút.
- `report/diagrams/*.mmd` — Sơ đồ Mermaid (flowchart hệ thống, data pipeline, logic quyết định).
- `images/*.png` — Toàn bộ biểu đồ phân tích và biểu đồ dự báo đã xuất sẵn.

---

## 8. Xác thực (Verification)

Toàn bộ project đã được kiểm thử chạy thực tế, không phát sinh lỗi:

| Kiểm thử | Kết quả |
|---|---|
| `python src/api.py` (với credentials giả) | Chạy xong, tự động fallback báo lỗi đúng thiết kế, exit code 0 |
| `python src/preprocess.py` | Sinh 500 dòng dữ liệu mô phỏng, exit code 0 |
| `python src/analysis.py` | In bảng thống kê + ma trận tương quan, exit code 0 |
| `python src/visualization.py` | Xuất đủ 7 biểu đồ PNG, exit code 0, không warning |
| `python src/prediction.py` | Huấn luyện mô hình, xuất biểu đồ dự báo, exit code 0 |
| `python src/irrigation_logic.py` | Chạy 3 ví dụ quyết định, exit code 0 |
| `notebook/smart_irrigation_analysis.ipynb` | Thực thi toàn bộ các ô lệnh tuần tự, không lỗi |
