"""
prediction.py
--------------
Module xây dựng mô hình AI dự báo đơn giản cho độ ẩm đất (Soil Moisture),
không sử dụng Deep Learning.

Kỹ thuật sử dụng:
    1. Moving Average (Trung bình trượt) — làm mượt dữ liệu, xác định xu hướng.
    2. Linear Regression (Hồi quy tuyến tính, scikit-learn) — dự báo giá trị
       tương lai và ước lượng thời điểm cần tưới tiếp theo.

Tác giả: Đồ án Hệ thống tưới cây thông minh ESP32 + ThingSpeak
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MOISTURE_THRESHOLD = 40.0  # Ngưỡng độ ẩm đất cần tưới (%)


def add_moving_average(df: pd.DataFrame, column: str = "soil_moisture", window: int = 8) -> pd.DataFrame:
    """Thêm cột Moving Average (trung bình trượt) vào DataFrame.

    Tham số:
        df: DataFrame chứa dữ liệu đã làm sạch.
        column: Tên cột cần tính trung bình trượt.
        window: Kích thước cửa sổ trượt (số bản ghi).

    Trả về:
        DataFrame mới có thêm cột f"{column}_ma".
    """
    result = df.copy()
    result[f"{column}_ma"] = result[column].rolling(window=window, min_periods=1, center=False).mean()
    return result


def detect_drying_trend(df: pd.DataFrame, column: str = "soil_moisture_ma", lookback: int = 6) -> bool:
    """Phát hiện xu hướng độ ẩm đất giảm liên tục (sắp khô) dựa trên Moving Average.

    Nếu `lookback` giá trị Moving Average gần nhất giảm dần liên tiếp,
    hệ thống coi là đang trong xu hướng khô và cần cảnh báo.

    Trả về:
        True nếu phát hiện xu hướng giảm liên tục, ngược lại False.
    """
    if column not in df.columns or len(df) < lookback:
        return False

    recent = df[column].tail(lookback).to_numpy()
    diffs = np.diff(recent)
    return bool(np.all(diffs < 0))


def train_linear_regression(
    df: pd.DataFrame, column: str = "soil_moisture"
) -> tuple[LinearRegression, dict]:
    """Huấn luyện mô hình Linear Regression: thời gian (index) -> độ ẩm đất.

    Mô hình đơn giản dùng biến độc lập là thứ tự thời gian (số bản ghi kể từ
    lúc bắt đầu), phù hợp làm baseline cho đồ án sinh viên.

    Trả về:
        (model, metrics) trong đó metrics gồm MAE, RMSE, R^2 trên chính tập huấn luyện.
    """
    X = np.arange(len(df)).reshape(-1, 1)  # Biến độc lập: chỉ số thời gian
    y = df[column].to_numpy()

    model = LinearRegression()
    model.fit(X, y)

    y_pred = model.predict(X)
    metrics = {
        "MAE": round(mean_absolute_error(y, y_pred), 3),
        "RMSE": round(np.sqrt(mean_squared_error(y, y_pred)), 3),
        "R2": round(r2_score(y, y_pred), 3),
        "he_so_goc_slope": round(float(model.coef_[0]), 5),
        "diem_cat_intercept": round(float(model.intercept_), 3),
    }
    return model, metrics


def forecast_future(
    model: LinearRegression,
    df: pd.DataFrame,
    steps_ahead: int,
    freq_minutes: int = 15,
) -> pd.DataFrame:
    """Dự báo giá trị độ ẩm đất cho `steps_ahead` bước tiếp theo bằng mô hình đã huấn luyện.

    Tham số:
        model: Mô hình LinearRegression đã huấn luyện bởi train_linear_regression().
        df: DataFrame dữ liệu lịch sử (dùng để lấy mốc thời gian cuối cùng).
        steps_ahead: Số bước (bản ghi) muốn dự báo về tương lai.
        freq_minutes: Khoảng cách thời gian giữa các bản ghi (phút).

    Trả về:
        DataFrame gồm [created_at, predicted_soil_moisture] cho các bước tương lai.
    """
    n = len(df)
    future_idx = np.arange(n, n + steps_ahead).reshape(-1, 1)
    predictions = model.predict(future_idx)
    predictions = np.clip(predictions, 0, 100)  # Độ ẩm đất luôn trong khoảng 0-100%

    last_time = df["created_at"].iloc[-1]
    future_times = pd.date_range(
        start=last_time, periods=steps_ahead + 1, freq=f"{freq_minutes}min"
    )[1:]

    return pd.DataFrame({"created_at": future_times, "predicted_soil_moisture": predictions})


def estimate_time_to_threshold(
    model: LinearRegression,
    df: pd.DataFrame,
    threshold: float = MOISTURE_THRESHOLD,
    freq_minutes: int = 15,
    max_steps: int = 3000,
) -> Optional[pd.Timestamp]:
    """Ước lượng thời điểm độ ẩm đất sẽ giảm xuống dưới ngưỡng cần tưới.

    Dựa trên xu hướng tuyến tính hiện tại (độ dốc của Linear Regression),
    ngoại suy tới thời điểm giá trị dự báo chạm ngưỡng `threshold`.

    Trả về:
        pd.Timestamp thời điểm dự kiến cần tưới, hoặc None nếu xu hướng không giảm
        (slope >= 0, tức độ ẩm không giảm) trong phạm vi max_steps bước dự báo.
    """
    forecast_df = forecast_future(model, df, steps_ahead=max_steps, freq_minutes=freq_minutes)
    below = forecast_df[forecast_df["predicted_soil_moisture"] <= threshold]

    if below.empty:
        return None
    return below.iloc[0]["created_at"]


def plot_prediction(
    df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    save_path: Optional[str] = None,
) -> None:
    """Vẽ biểu đồ Actual / Moving Average (Trend) / Prediction trên cùng một hình."""
    fig, ax = plt.subplots(figsize=(12, 5.5))

    ax.plot(df["created_at"], df["soil_moisture"], color="#2A9D8F", linewidth=1.2, alpha=0.6, label="Actual (Thực tế)")

    if "soil_moisture_ma" in df.columns:
        ax.plot(df["created_at"], df["soil_moisture_ma"], color="#264653", linewidth=2, label="Trend (Moving Average)")

    ax.plot(
        forecast_df["created_at"],
        forecast_df["predicted_soil_moisture"],
        color="#E76F51",
        linewidth=2,
        linestyle="--",
        label="Prediction (Linear Regression)",
    )

    ax.axhline(MOISTURE_THRESHOLD, color="red", linestyle=":", linewidth=1.2, label=f"Ngưỡng tưới ({MOISTURE_THRESHOLD}%)")

    ax.set_title("Dự báo xu hướng Độ ẩm đất (Actual vs Trend vs Prediction)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Độ ẩm đất (%)")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
        print(f"[prediction.py] Đã lưu biểu đồ dự báo: {save_path}")
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    df = pd.read_csv("../data/simulated_data.csv", parse_dates=["created_at"])
    df = add_moving_average(df, "soil_moisture", window=8)

    model, metrics = train_linear_regression(df, "soil_moisture")
    print("Chỉ số đánh giá mô hình Linear Regression:", metrics)

    drying = detect_drying_trend(df)
    print("Xu hướng đang khô liên tục?", drying)

    forecast_df = forecast_future(model, df, steps_ahead=48, freq_minutes=15)
    next_watering = estimate_time_to_threshold(model, df, freq_minutes=15)
    print("Thời điểm dự kiến cần tưới tiếp theo:", next_watering)

    plot_prediction(df, forecast_df, save_path="../images/08_prediction_soil_moisture.png")
