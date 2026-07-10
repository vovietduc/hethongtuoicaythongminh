#define BLYNK_PRINT Serial
#include <WiFi.h>
#include <WiFiClient.h>
#include "config.h"        // <- ĐẶT NGAY TRƯỚC Blynk
#include <BlynkSimpleEsp32.h>
#include "ThingSpeak.h"

// ------------------ Khởi tạo đối tượng ------------------
WiFiClient espClient;
BlynkTimer timer;

// ------------------ Biến trạng thái hệ thống ------------------
bool pumpState = false;
bool manualMode = false;
bool rainDetected = false;

int soilMoisture = 50;
int temperature = 28;
int airHumidity = 65;
int rainADC = 2500;

// ------------------ HÀM XỬ LÝ MẤT WIFI ------------------
void ensureWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Mất kết nối WiFi. Đang thử kết nối lại...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(200);
      Serial.print(".");
      attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n✅ WiFi đã kết nối lại thành công!");
      Blynk.connect();
    } else {
      Serial.println("\n❌ Không thể kết nối lại WiFi. Thử lại sau.");
    }
  }
}

// ------------------ NHẬN LỆNH ĐIỀU KHIỂN TỪ BLYNK ------------------
BLYNK_WRITE(VPIN_PUMP_CONTROL) {
  if (manualMode) {
    int cmd = param.asInt();
    controlPump(cmd);
    Serial.print("🖐️ MANUAL: Lệnh từ Dashboard -> Bơm ");
    Serial.println(cmd ? "BẬT" : "TẮT");
  } else {
    Serial.println("⛔ Đang ở chế độ AUTO, bỏ qua lệnh thủ công.");
  }
}

BLYNK_WRITE(VPIN_SYSTEM_MODE) {
  manualMode = param.asInt();
  Serial.print("🔀 Chuyển sang chế độ: ");
  Serial.println(manualMode ? "MANUAL (Thủ công)" : "AUTO (Tự động)");
  if (!manualMode) {
    autoControlPump();
  }
}

// ------------------ HÀM ĐIỀU KHIỂN BƠM ------------------
void controlPump(int state) {
  pumpState = state;
  digitalWrite(RELAY_PIN, state ? HIGH : LOW);
  Blynk.virtualWrite(VPIN_PUMP_STATUS, state ? 1 : 0);
  if (state) {
    Blynk.logEvent("pump_on", "Bơm được kích hoạt");
  } else {
    Blynk.logEvent("pump_off", "Bơm dừng hoạt động");
  }
}

// ------------------ LOGIC TỰ ĐỘNG ------------------
void autoControlPump() {
  if (manualMode) return;
  bool shouldTurnOn = (soilMoisture < MOISTURE_THRESHOLD_DRY) && !rainDetected;
  bool shouldTurnOff = (soilMoisture > MOISTURE_THRESHOLD_WET) || rainDetected;
  if (shouldTurnOn && !pumpState) {
    controlPump(HIGH);
    Serial.println("🌱 AUTO: Đất khô, trời không mưa -> BẬT BƠM");
  } else if (shouldTurnOff && pumpState) {
    controlPump(LOW);
    if (rainDetected) {
      Serial.println("🌧️ AUTO: Trời đang mưa -> TẮT BƠM");
    } else {
      Serial.println("✅ AUTO: Đất đủ ẩm -> TẮT BƠM");
    }
  }
}

// ------------------ ĐỌC CẢM BIẾN (Mô phỏng / Thực) ------------------
void readSensors() {
  // --- Mô phỏng (mặc định) ---
  #ifdef SIMULATION_MODE
    soilMoisture = random(20, 81);
    rainADC = random(200, 3500);
    temperature = random(25, 35);
    airHumidity = random(55, 80);
  #else
    // --- Thực tế ---
    int rawSoil = analogRead(SOIL_MOISTURE_PIN);
    soilMoisture = map(rawSoil, 0, 4095, 100, 0);
    soilMoisture = constrain(soilMoisture, 0, 100);
    rainADC = analogRead(RAIN_SENSOR_PIN);
    // Giả lập DHT nếu chưa có thư viện
    temperature = random(25, 35);
    airHumidity = random(55, 80);
  #endif

  rainDetected = (rainADC < RAIN_THRESHOLD);

  Serial.print("🌱 Đất: ");
  Serial.print(soilMoisture);
  Serial.print("% | 🌧️ Mưa: ");
  Serial.print(rainDetected ? "CÓ" : "KHÔNG");
  Serial.print(" (ADC:");
  Serial.print(rainADC);
  Serial.print(") | 🌡️ ");
  Serial.print(temperature);
  Serial.print("°C | 💧 ");
  Serial.print(airHumidity);
  Serial.println("%");
}

// ------------------ GỬI LÊN BLYNK ------------------
void sendToBlynk() {
  Blynk.virtualWrite(VPIN_SOIL_MOISTURE, soilMoisture);
  Blynk.virtualWrite(VPIN_TEMPERATURE, temperature);
  Blynk.virtualWrite(VPIN_HUMIDITY, airHumidity);
  Blynk.virtualWrite(VPIN_RAIN_STATUS, rainDetected ? 1 : 0);
  Blynk.virtualWrite(VPIN_PUMP_STATUS, pumpState ? 1 : 0);
  Blynk.virtualWrite(VPIN_SYSTEM_MODE, manualMode ? 1 : 0);
}

// ------------------ GỬI LÊN THINGSPEAK ------------------
void sendToThingSpeak() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ Mất WiFi, bỏ qua gửi ThingSpeak lần này.");
    return;
  }
  // Field 1: Độ ẩm đất, Field 2: Nhiệt độ, Field 3: Độ ẩm không khí,
  // Field 4: Trạng thái bơm, Field 5: Trạng thái mưa
  ThingSpeak.setField(1, soilMoisture);
  ThingSpeak.setField(2, temperature);
  ThingSpeak.setField(3, airHumidity);
  ThingSpeak.setField(4, pumpState ? 1 : 0);
  ThingSpeak.setField(5, rainDetected ? 1 : 0);

  int statusCode = ThingSpeak.writeFields(TS_CHANNEL_ID, TS_WRITE_API_KEY);
  if (statusCode == 200) {
    Serial.println("📊 ThingSpeak: Cập nhật thành công!");
  } else {
    Serial.print("❌ ThingSpeak: Lỗi HTTP ");
    Serial.println(statusCode);
  }
}

// ------------------ TIMER TỔNG HỢP ------------------
void timerEvent() {
  readSensors();
  autoControlPump();
  sendToBlynk();
}

// ------------------ SETUP ------------------
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(RAIN_SENSOR_PIN, INPUT);

  Serial.print("📶 Đang kết nối WiFi ");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi đã kết nối! IP: " + WiFi.localIP().toString());

  ThingSpeak.begin(espClient);
  Blynk.config(BLYNK_AUTH_TOKEN);
  Blynk.connect();

  timer.setInterval(BLYNK_UPDATE_INTERVAL, timerEvent);
  timer.setInterval(THINGSPEAK_INTERVAL, sendToThingSpeak);

  Serial.println("🚀 HỆ THỐNG ĐÃ SẴN SÀNG!");
  Serial.println("========================================");
}

// ------------------ LOOP ------------------
void loop() {
  ensureWiFiConnection();
  Blynk.run();
  timer.run();
}