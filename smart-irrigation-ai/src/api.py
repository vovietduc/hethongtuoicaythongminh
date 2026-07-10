"""
api.py
------
Module chịu trách nhiệm thu thập dữ liệu từ ThingSpeak Cloud.

Chức năng chính:
    - Gọi ThingSpeak REST API để lấy dữ liệu cảm biến (channel feeds).
    - Chuyển đổi dữ liệu JSON trả về thành pandas DataFrame.
    - Xử lý các lỗi phổ biến khi gọi API (timeout, sai key, không có dữ liệu...).
    - Ép kiểu dữ liệu (numeric) và chuyển cột created_at sang kiểu datetime.
    - Loại bỏ các bản ghi rỗng / không hợp lệ.

Tác giả: Đồ án Hệ thống tưới cây thông minh ESP32 + ThingSpeak
"""

from __future__ import annotations

import time
from typing import Optional

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Cấu hình mặc định
# ---------------------------------------------------------------------------

# Mapping giữa tên field trên ThingSpeak và tên cột dễ đọc trong DataFrame.
FIELD_MAPPING = {
    "field1": "temperature",     # Nhiệt độ (°C)
    "field2": "soil_moisture",   # Độ ẩm đất (%)
    "field3": "air_humidity",    # Độ ẩm không khí (%)
    "field4": "light_intensity", # Cường độ ánh sáng (lux hoặc %)
    "field5": "pump_status",     # Trạng thái bơm (0 = OFF, 1 = ON)
}

DEFAULT_TIMEOUT_SEC = 10  # Thời gian chờ tối đa khi gọi API (giây)


class ThingSpeakAPIError(Exception):
    """Ngoại lệ tùy biến cho các lỗi liên quan đến ThingSpeak API."""


def fetch_thingspeak_data(
    channel_id: str,
    read_api_key: Optional[str] = None,
    results: int = 500,
    timeout: int = DEFAULT_TIMEOUT_SEC,
    max_retries: int = 3,
) -> pd.DataFrame:
    """Lấy dữ liệu feeds từ một ThingSpeak channel và trả về DataFrame đã chuẩn hóa.

    Tham số:
        channel_id: Mã channel ThingSpeak (ví dụ: "123456").
        read_api_key: API Key dùng để đọc dữ liệu (bắt buộc nếu channel ở chế độ Private).
        results: Số bản ghi gần nhất muốn lấy (ThingSpeak giới hạn tối đa 8000).
        timeout: Thời gian chờ tối đa (giây) cho mỗi request.
        max_retries: Số lần thử lại nếu request thất bại.

    Trả về:
        pandas.DataFrame với các cột:
        [created_at, entry_id, temperature, soil_moisture,
         air_humidity, light_intensity, pump_status]

    Ngoại lệ:
        ThingSpeakAPIError: khi không thể lấy được dữ liệu hợp lệ sau nhiều lần thử.
    """
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    params = {"results": results}
    if read_api_key:
        params["api_key"] = read_api_key

    last_error: Optional[Exception] = None

    # Thử gọi API tối đa `max_retries` lần để tăng độ ổn định khi mạng chập chờn.
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()  # Ném lỗi nếu status code là 4xx/5xx
            payload = response.json()

            feeds = payload.get("feeds")
            if not feeds:
                raise ThingSpeakAPIError(
                    "API trả về thành công nhưng không có dữ liệu (feeds rỗng). "
                    "Kiểm tra lại Channel ID / API Key."
                )

            return _feeds_to_dataframe(feeds)

        except (requests.exceptions.RequestException, ValueError) as exc:
            # RequestException: lỗi mạng/timeout/HTTP.
            # ValueError: lỗi khi parse JSON không hợp lệ.
            last_error = exc
            if attempt < max_retries:
                time.sleep(1.5 * attempt)  # Backoff tăng dần trước khi thử lại
                continue

    # Nếu tới đây nghĩa là đã hết số lần thử mà vẫn lỗi.
    raise ThingSpeakAPIError(
        f"Không thể lấy dữ liệu từ ThingSpeak sau {max_retries} lần thử. "
        f"Lỗi cuối cùng: {last_error}"
    )


def _feeds_to_dataframe(feeds: list[dict]) -> pd.DataFrame:
    """Chuyển danh sách feeds (JSON) từ ThingSpeak thành DataFrame đã làm sạch cơ bản.

    Bước xử lý:
        1. Tạo DataFrame thô từ JSON.
        2. Đổi tên cột field1..field5 thành tên có ý nghĩa.
        3. Ép kiểu dữ liệu số cho các cột cảm biến.
        4. Chuyển created_at sang kiểu datetime.
        5. Loại bỏ các dòng thiếu dữ liệu hoàn toàn (tất cả field đều rỗng).
    """
    df = pd.DataFrame(feeds)

    # Đổi tên cột field1..field5 -> tên có ý nghĩa (nếu cột tồn tại).
    df = df.rename(columns=FIELD_MAPPING)

    # Ép kiểu numeric cho từng cột cảm biến; giá trị không hợp lệ -> NaN.
    numeric_cols = list(FIELD_MAPPING.values())
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Chuyển created_at (chuỗi ISO 8601 UTC) sang kiểu datetime của pandas.
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)

    # Loại bỏ các dòng mà TẤT CẢ các cột cảm biến đều là NaN (dòng hoàn toàn rỗng).
    df = df.dropna(how="all", subset=[c for c in numeric_cols if c in df.columns])

    # Sắp xếp theo thời gian tăng dần và reset lại index.
    if "created_at" in df.columns:
        df = df.sort_values("created_at").reset_index(drop=True)

    return df


def save_raw_data(df: pd.DataFrame, path: str) -> None:
    """Lưu DataFrame thô ra file CSV để tái sử dụng / kiểm tra thủ công."""
    df.to_csv(path, index=False)
    print(f"[api.py] Đã lưu {len(df)} dòng dữ liệu vào: {path}")


if __name__ == "__main__":
    # Ví dụ chạy thử độc lập (cần thay CHANNEL_ID và API_KEY thật).
    CHANNEL_ID = "YOUR_CHANNEL_ID"
    READ_API_KEY = "YOUR_READ_API_KEY"

    try:
        data = fetch_thingspeak_data(CHANNEL_ID, READ_API_KEY, results=500)
        print(data.head())
        save_raw_data(data, "../data/raw_data.csv")
    except ThingSpeakAPIError as err:
        print(f"Lỗi khi lấy dữ liệu: {err}")
        print("Gợi ý: dùng preprocess.generate_simulated_data() để tạo dữ liệu mô phỏng.")
