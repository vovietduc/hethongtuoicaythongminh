"""
preprocess.py
-------------
Module tiền xử lý dữ liệu cảm biến và sinh dữ liệu mô phỏng.

Chức năng chính:
    - Làm sạch dữ liệu: loại bỏ trùng lặp, giá trị ngoại lai (outlier), giá trị thiếu.
    - Nội suy (interpolate) các giá trị bị thiếu để đảm bảo chuỗi thời gian liên tục.
    - Sinh dữ liệu mô phỏng ~500 dòng, có tính chu kỳ ngày/đêm giống thực tế,
      dùng khi chưa kết nối được ThingSpeak thật.

Tác giả: Đồ án Hệ thống tưới cây thông minh ESP32 + ThingSpeak
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SENSOR_COLUMNS = [
    "temperature",
    "soil_moisture",
    "air_humidity",
    "light_intensity",
    "pump_status",
]

# Giới hạn vật lý hợp lý dùng để phát hiện outlier (dữ liệu ngoài khoảng này là vô lý).
PHYSICAL_LIMITS = {
    "temperature": (0, 60),        # °C
    "soil_moisture": (0, 100),     # %
    "air_humidity": (0, 100),      # %
    "light_intensity": (0, 100000),  # lux (tùy cảm biến, nới rộng)
}


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch dữ liệu cảm biến thô.

    Các bước:
        1. Xóa các dòng trùng lặp hoàn toàn.
        2. Loại bỏ các dòng thiếu created_at (không xác định được thời gian).
        3. Loại bỏ outlier vượt giới hạn vật lý hợp lý (thay bằng NaN).
        4. Nội suy tuyến tính (interpolate) các giá trị NaN theo thời gian.
        5. Loại bỏ các dòng vẫn còn NaN sau khi nội suy (ví dụ ở đầu/cuối chuỗi).

    Tham số:
        df: DataFrame dữ liệu thô (đầu ra của api.py).

    Trả về:
        DataFrame đã được làm sạch, sẵn sàng cho bước phân tích.
    """
    clean = df.copy()

    # 1. Xóa dòng trùng lặp hoàn toàn.
    before = len(clean)
    clean = clean.drop_duplicates()
    removed_dup = before - len(clean)

    # 2. Loại bỏ dòng thiếu created_at.
    if "created_at" in clean.columns:
        clean = clean.dropna(subset=["created_at"])

    # 3. Loại bỏ outlier: đưa giá trị ngoài giới hạn vật lý thành NaN.
    outlier_count = 0
    for col, (low, high) in PHYSICAL_LIMITS.items():
        if col in clean.columns:
            mask = ~clean[col].between(low, high)
            outlier_count += int(mask.sum())
            clean.loc[mask, col] = np.nan

    # 4. Nội suy tuyến tính theo thứ tự thời gian cho các cột số.
    numeric_cols = [c for c in SENSOR_COLUMNS if c in clean.columns]
    clean[numeric_cols] = clean[numeric_cols].interpolate(
        method="linear", limit_direction="both"
    )

    # 5. Loại bỏ các dòng vẫn còn thiếu dữ liệu (không thể nội suy được).
    before_final = len(clean)
    clean = clean.dropna(subset=numeric_cols)
    removed_na = before_final - len(clean)

    clean = clean.reset_index(drop=True)

    print(
        "[preprocess.py] Làm sạch dữ liệu hoàn tất: "
        f"loại {removed_dup} dòng trùng lặp, "
        f"phát hiện {outlier_count} giá trị outlier, "
        f"loại {removed_na} dòng không thể khôi phục. "
        f"Còn lại {len(clean)} dòng hợp lệ."
    )
    return clean


def generate_simulated_data(
    n_rows: int = 500,
    start_time: str = "2026-06-01 00:00:00",
    freq_minutes: int = 15,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Sinh dữ liệu mô phỏng giống dữ liệu cảm biến thực tế của hệ thống tưới cây.

    Mô hình mô phỏng:
        - Nhiệt độ và ánh sáng dao động theo chu kỳ ngày/đêm (hàm sin theo giờ trong ngày).
        - Độ ẩm đất giảm dần theo thời gian do bốc hơi, và tăng đột biến khi bơm bật (tưới).
        - Độ ẩm không khí tỉ lệ nghịch nhẹ với nhiệt độ + nhiễu ngẫu nhiên.
        - Bơm (pump_status) tự động bật khi độ ẩm đất xuống dưới ngưỡng 40%.

    Tham số:
        n_rows: Số dòng dữ liệu cần sinh (mặc định 500).
        start_time: Thời điểm bắt đầu của chuỗi thời gian.
        freq_minutes: Khoảng cách giữa 2 bản ghi liên tiếp (phút).
        random_seed: Seed cho bộ sinh số ngẫu nhiên để đảm bảo tái lập được kết quả.

    Trả về:
        DataFrame mô phỏng với các cột: created_at, entry_id, temperature,
        soil_moisture, air_humidity, light_intensity, pump_status.
    """
    rng = np.random.default_rng(random_seed)

    timestamps = pd.date_range(start=start_time, periods=n_rows, freq=f"{freq_minutes}min")
    hour_of_day = timestamps.hour + timestamps.minute / 60.0

    # --- Nhiệt độ: dao động 22-35°C theo chu kỳ ngày/đêm (đỉnh vào ~14h) ---
    temperature = 28 + 6 * np.sin((hour_of_day - 8) / 24 * 2 * np.pi) + rng.normal(0, 0.8, n_rows)
    temperature = np.clip(temperature, 18, 40)

    # --- Ánh sáng: 0 vào ban đêm, đạt đỉnh giữa trưa ---
    daylight = np.clip(np.sin((hour_of_day - 6) / 12 * np.pi), 0, 1)
    light_intensity = daylight * 20000 + rng.normal(0, 300, n_rows)
    light_intensity = np.clip(light_intensity, 0, 20000)

    # --- Độ ẩm không khí: tỉ lệ nghịch nhẹ với nhiệt độ ---
    air_humidity = 85 - (temperature - 22) * 1.5 + rng.normal(0, 3, n_rows)
    air_humidity = np.clip(air_humidity, 30, 95)

    # --- Độ ẩm đất: giảm dần do bốc hơi, tăng vọt khi bơm tưới ---
    soil_moisture = np.zeros(n_rows)
    pump_status = np.zeros(n_rows, dtype=int)

    soil_moisture[0] = 65.0  # Giá trị khởi tạo ban đầu
    for i in range(1, n_rows):
        # Tốc độ bốc hơi tăng khi trời nóng và nắng nhiều.
        evaporation = 0.15 + 0.05 * (temperature[i] / 30) + 0.05 * daylight[i]
        noise = rng.normal(0, 0.3)
        value = soil_moisture[i - 1] - evaporation + noise

        # Nếu độ ẩm đất xuống dưới 40% -> bơm tự động bật, độ ẩm tăng vọt.
        if value < 40:
            pump_status[i] = 1
            value += rng.uniform(15, 25)  # Lượng nước tưới bổ sung
        else:
            pump_status[i] = 0

        soil_moisture[i] = np.clip(value, 15, 90)

    df = pd.DataFrame(
        {
            "created_at": timestamps,
            "entry_id": np.arange(1, n_rows + 1),
            "temperature": np.round(temperature, 2),
            "soil_moisture": np.round(soil_moisture, 2),
            "air_humidity": np.round(air_humidity, 2),
            "light_intensity": np.round(light_intensity, 1),
            "pump_status": pump_status,
        }
    )

    print(f"[preprocess.py] Đã sinh {len(df)} dòng dữ liệu mô phỏng (seed={random_seed}).")
    return df


if __name__ == "__main__":
    simulated = generate_simulated_data(500)
    simulated.to_csv("../data/simulated_data.csv", index=False)
    print(simulated.describe())
