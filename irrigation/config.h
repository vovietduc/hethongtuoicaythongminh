#ifndef CONFIG_H
#define CONFIG_H

// ===== WIFI =====
const char* WIFI_SSID     = "Wokwi-GUEST";   // Đổi thành WiFi thật
const char* WIFI_PASSWORD = "";

// ===== BLYNK =====
#define BLYNK_TEMPLATE_ID   "TMPL6z84sJp6S"
#define BLYNK_TEMPLATE_NAME "HeThongTuoiCayThongMinh"
#define BLYNK_AUTH_TOKEN    "MIu0zmG8Ju1jaoFzT_pbKRDcKGkj0smm"

// ===== THINGSPEAK =====
#define TS_CHANNEL_ID       3420737          // Thay bằng Channel ID từ Đức
#define TS_WRITE_API_KEY    "NYKUBQU61JY56GZ9"   // Thay bằng Write API Key từ Đức

// ===== VIRTUAL PIN =====
#define VPIN_SOIL_MOISTURE  V0
#define VPIN_PUMP_STATUS    V1
#define VPIN_RAIN_STATUS    V2
#define VPIN_PUMP_CONTROL   V3
#define VPIN_TEMPERATURE    V4
#define VPIN_HUMIDITY       V5
#define VPIN_SYSTEM_MODE    V6

// ===== GPIO =====
#define SOIL_MOISTURE_PIN   34
#define RAIN_SENSOR_PIN     35
#define RELAY_PIN           19
#define DHT_PIN             13

// ===== NGƯỠNG =====
#define MOISTURE_THRESHOLD_DRY   30
#define MOISTURE_THRESHOLD_WET   70
#define RAIN_THRESHOLD           800

// ===== THỜI GIAN =====
#define BLYNK_UPDATE_INTERVAL    2000
#define THINGSPEAK_INTERVAL      20000

#endif