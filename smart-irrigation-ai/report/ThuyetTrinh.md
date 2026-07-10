# Kịch bản thuyết trình (~3 phút)
## Đề tài: Hệ thống tưới cây thông minh sử dụng ESP32 + ThingSpeak — Phần Phân tích dữ liệu & AI

---

**[0:00 – 0:25] Mở đầu**

Xin chào thầy/cô và các bạn. Nhóm em xin trình bày phần **Phân tích dữ liệu và AI**
trong đề tài "Hệ thống tưới cây thông minh sử dụng ESP32 và ThingSpeak". Phần mềm
ESP32 thu thập 5 thông số: nhiệt độ, độ ẩm đất, độ ẩm không khí, cường độ ánh sáng
và trạng thái bơm, sau đó gửi lên nền tảng ThingSpeak. Nhiệm vụ của nhóm em là xử lý,
phân tích dữ liệu này bằng Python và xây dựng AI để tự động ra quyết định tưới cây.

**[0:25 – 0:55] Thu thập và tiền xử lý dữ liệu**

Đầu tiên, hệ thống gọi ThingSpeak REST API để lấy dữ liệu dạng JSON, sau đó chuyển
thành bảng dữ liệu bằng thư viện pandas. Vì dữ liệu cảm biến thực tế thường có nhiễu,
nhóm em xây dựng bước tiền xử lý gồm: loại bỏ dữ liệu trùng lặp, loại bỏ giá trị vượt
ngưỡng vật lý hợp lý, và nội suy các giá trị bị thiếu để đảm bảo chuỗi thời gian liên
tục. Trong trường hợp chưa kết nối được phần cứng thật, nhóm em cũng xây dựng một bộ
sinh dữ liệu mô phỏng gồm 500 dòng, mô phỏng đúng chu kỳ ngày – đêm và quá trình bốc
hơi nước trong đất.

**[0:55 – 1:30] Phân tích và trực quan hóa**

Sau khi làm sạch, nhóm em tính các chỉ số thống kê cơ bản như trung bình, giá trị
nhỏ nhất – lớn nhất, độ lệch chuẩn và trung vị cho nhiệt độ, độ ẩm đất và độ ẩm
không khí. Để hiểu rõ hơn xu hướng dữ liệu, nhóm em xây dựng 7 loại biểu đồ: biểu đồ
đường theo thời gian cho từng thông số, biểu đồ so sánh nhiệt độ và độ ẩm đất,
histogram và boxplot cho độ ẩm đất, cùng với ma trận tương quan (correlation
heatmap) để xem thông số nào ảnh hưởng lẫn nhau — ví dụ nhiệt độ và độ ẩm không khí
có tương quan nghịch khá rõ.

**[1:30 – 2:15] AI dự báo nhu cầu tưới cây**

Đây là phần trọng tâm của đề tài. Thay vì dùng mô hình Deep Learning phức tạp, nhóm
em lựa chọn hai kỹ thuật đơn giản nhưng hiệu quả: **Moving Average** để làm mượt dữ
liệu và xác định xu hướng, và **Linear Regression** của scikit-learn để dự báo giá
trị độ ẩm đất trong tương lai. Từ đường xu hướng này, hệ thống có thể ước lượng
được thời điểm dự kiến độ ẩm đất sẽ giảm xuống dưới ngưỡng cần tưới, giúp chủ động
lên kế hoạch tưới nước thay vì chỉ phản ứng khi đất đã khô.

**[2:15 – 2:45] Thuật toán quyết định điều khiển bơm**

Dựa trên kết quả phân tích và dự báo, nhóm em xây dựng thuật toán quyết định theo
3 quy tắc: nếu độ ẩm đất dưới 40% thì bật bơm; nếu trên 60% thì tắt bơm; còn nếu
Moving Average cho thấy độ ẩm đang giảm liên tục, hệ thống sẽ phát cảnh báo sớm là
đất sắp khô, ngay cả khi độ ẩm hiện tại chưa xuống dưới ngưỡng.

**[2:45 – 3:00] Kết luận**

Tóm lại, module phân tích dữ liệu và AI mà nhóm em xây dựng đã hoàn chỉnh pipeline
từ thu thập, làm sạch, phân tích, trực quan hóa cho đến dự báo và ra quyết định tự
động, góp phần giúp hệ thống tưới cây thông minh hoạt động hiệu quả và tiết kiệm
nước hơn. Hướng phát triển tiếp theo là tích hợp thêm dữ liệu thời tiết và mô hình
học máy nâng cao hơn. Em xin cảm ơn thầy/cô và các bạn đã lắng nghe.
