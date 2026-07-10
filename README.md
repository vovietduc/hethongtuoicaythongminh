# hethongtuoicaythongminh
#define BLYNK_TEMPLATE_ID   "TMPLxxxxxx"      // Lấy trong Blynk Console > Template
#define BLYNK_TEMPLATE_NAME "Smart Irrigation"
#define BLYNK_AUTH_TOKEN    "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  // Token của Device trong Blynk

// Thông tin WiFi (dùng để mô phỏng, có thể để tên WiFi thật của máy chạy giả lập)
char ssid[] = "Ten_WiFi";
char pass[] = "Mat_khau_WiFi";

// Virtual Pin mapping (theo bảng đã thống nhất)
#define VPIN_TEMP     V0   // Nhiệt độ
#define VPIN_HUMID    V1   // Độ ẩm không khí
#define VPIN_PRESSURE V2   // Áp suất
#define VPIN_SOIL     V3   // Độ ẩm đất
#define VPIN_RAIN     V4   // Cảm biến mưa
#define VPIN_PUMP     V5   // Relay/bơm
#define VPIN_TIME     V6   // RTC
