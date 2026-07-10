"""
analysis.py
-----------
Module phân tích thống kê mô tả cho dữ liệu cảm biến đã làm sạch.

Chức năng chính:
    - Tính các đại lượng thống kê: trung bình, min, max, độ lệch chuẩn, trung vị.
    - In kết quả dưới dạng bảng dễ đọc.
    - Tính ma trận tương quan giữa các biến cảm biến.

Tác giả: Đồ án Hệ thống tưới cây thông minh ESP32 + ThingSpeak
"""

from __future__ import annotations

import pandas as pd

# Các cột sẽ được thống kê mô tả và tên hiển thị tiếng Việt tương ứng.
ANALYSIS_TARGETS = {
    "temperature": "Nhiệt độ (°C)",
    "soil_moisture": "Độ ẩm đất (%)",
    "air_humidity": "Độ ẩm không khí (%)",
}


def compute_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Tính các chỉ số thống kê mô tả (mean, min, max, std, median) cho các cột cảm biến.

    Tham số:
        df: DataFrame dữ liệu đã làm sạch.

    Trả về:
        DataFrame tổng hợp thống kê, mỗi dòng là một biến (nhiệt độ, độ ẩm đất, ...).
    """
    rows = []
    for col, label in ANALYSIS_TARGETS.items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        rows.append(
            {
                "Biến": label,
                "Trung bình": round(series.mean(), 2),
                "Nhỏ nhất": round(series.min(), 2),
                "Lớn nhất": round(series.max(), 2),
                "Độ lệch chuẩn": round(series.std(), 2),
                "Trung vị": round(series.median(), 2),
            }
        )
    return pd.DataFrame(rows)


def print_statistics(stats: pd.DataFrame) -> None:
    """In bảng thống kê ra màn hình dưới định dạng dễ đọc."""
    print("\n" + "=" * 78)
    print("BẢNG THỐNG KÊ MÔ TẢ DỮ LIỆU CẢM BIẾN")
    print("=" * 78)
    print(stats.to_string(index=False))
    print("=" * 78 + "\n")


def compute_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Tính ma trận tương quan Pearson giữa các biến cảm biến số.

    Tham số:
        df: DataFrame dữ liệu đã làm sạch.

    Trả về:
        DataFrame ma trận tương quan (giá trị từ -1 đến 1).
    """
    numeric_cols = ["temperature", "soil_moisture", "air_humidity", "light_intensity"]
    cols = [c for c in numeric_cols if c in df.columns]
    return df[cols].corr()


def summarize_pump_activity(df: pd.DataFrame) -> dict:
    """Tổng hợp thông tin về hoạt động của máy bơm trong tập dữ liệu.

    Trả về dict gồm: tổng số lần bơm bật, tỉ lệ thời gian bơm hoạt động (%).
    """
    if "pump_status" not in df.columns:
        return {}

    total = len(df)
    pump_on_count = int((df["pump_status"] == 1).sum())
    # Đếm số "lượt" bơm bật (chuyển từ 0 sang 1) thay vì số bản ghi có giá trị 1.
    transitions = df["pump_status"].diff().fillna(0)
    pump_on_events = int((transitions == 1).sum())

    return {
        "tong_ban_ghi": total,
        "so_ban_ghi_bom_bat": pump_on_count,
        "ti_le_thoi_gian_bom_hoat_dong_%": round(pump_on_count / total * 100, 2),
        "so_lan_bom_duoc_kich_hoat": pump_on_events,
    }


if __name__ == "__main__":
    df = pd.read_csv("../data/simulated_data.csv", parse_dates=["created_at"])
    stats = compute_statistics(df)
    print_statistics(stats)
    print("Ma trận tương quan:")
    print(compute_correlation_matrix(df).round(2))
    print("\nHoạt động bơm:")
    print(summarize_pump_activity(df))
