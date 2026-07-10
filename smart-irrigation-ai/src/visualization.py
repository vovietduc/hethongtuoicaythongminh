"""
visualization.py
-----------------
Module trực quan hóa dữ liệu cảm biến bằng matplotlib.

Chức năng chính:
    - Vẽ biểu đồ đường theo thời gian (nhiệt độ, độ ẩm đất, độ ẩm không khí).
    - Vẽ biểu đồ so sánh Temperature vs Soil Moisture (2 trục y).
    - Vẽ Histogram và Boxplot cho Soil Moisture.
    - Vẽ Correlation Heatmap (dùng matplotlib thuần, không bắt buộc seaborn).

Ghi chú: Toàn bộ biểu đồ dùng matplotlib. Nếu môi trường có sẵn seaborn,
có thể thay heatmap bằng `sns.heatmap()` để đẹp hơn, nhưng không bắt buộc.

Tác giả: Đồ án Hệ thống tưới cây thông minh ESP32 + ThingSpeak
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Bảng màu chủ đạo dùng xuyên suốt các biểu đồ để đồng bộ giao diện.
COLOR_TEMPERATURE = "#E76F51"
COLOR_SOIL_MOISTURE = "#2A9D8F"
COLOR_AIR_HUMIDITY = "#264653"
COLOR_ACCENT = "#F4A261"

plt.rcParams.update(
    {
        "figure.figsize": (11, 5),
        "figure.dpi": 110,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "font.size": 11,
    }
)


def _save_or_show(fig: plt.Figure, save_path: str | None) -> None:
    """Lưu biểu đồ ra file nếu có save_path, ngược lại hiển thị trực tiếp."""
    fig.tight_layout()
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.savefig(save_path, bbox_inches="tight")
        print(f"[visualization.py] Đã lưu biểu đồ: {save_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_temperature_over_time(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ biểu đồ Temperature theo thời gian."""
    fig, ax = plt.subplots()
    ax.plot(df["created_at"], df["temperature"], color=COLOR_TEMPERATURE, linewidth=1.5, label="Nhiệt độ (°C)")
    ax.set_title("Nhiệt độ theo thời gian", fontsize=14, fontweight="bold")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Nhiệt độ (°C)")
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    _save_or_show(fig, save_path)


def plot_soil_moisture_over_time(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ biểu đồ Soil Moisture theo thời gian, có đường ngưỡng tưới 40%."""
    fig, ax = plt.subplots()
    ax.plot(df["created_at"], df["soil_moisture"], color=COLOR_SOIL_MOISTURE, linewidth=1.5, label="Độ ẩm đất (%)")
    ax.axhline(40, color="red", linestyle="--", linewidth=1, label="Ngưỡng cần tưới (40%)")
    ax.set_title("Độ ẩm đất theo thời gian", fontsize=14, fontweight="bold")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Độ ẩm đất (%)")
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    _save_or_show(fig, save_path)


def plot_humidity_over_time(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ biểu đồ Air Humidity theo thời gian."""
    fig, ax = plt.subplots()
    ax.plot(df["created_at"], df["air_humidity"], color=COLOR_AIR_HUMIDITY, linewidth=1.5, label="Độ ẩm không khí (%)")
    ax.set_title("Độ ẩm không khí theo thời gian", fontsize=14, fontweight="bold")
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Độ ẩm không khí (%)")
    ax.legend(loc="upper right")
    fig.autofmt_xdate()
    _save_or_show(fig, save_path)


def plot_temperature_vs_soil_moisture(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ biểu đồ so sánh Temperature và Soil Moisture trên 2 trục y."""
    fig, ax1 = plt.subplots()

    ax1.plot(df["created_at"], df["temperature"], color=COLOR_TEMPERATURE, linewidth=1.5, label="Nhiệt độ (°C)")
    ax1.set_xlabel("Thời gian")
    ax1.set_ylabel("Nhiệt độ (°C)", color=COLOR_TEMPERATURE)
    ax1.tick_params(axis="y", labelcolor=COLOR_TEMPERATURE)

    ax2 = ax1.twinx()
    ax2.plot(df["created_at"], df["soil_moisture"], color=COLOR_SOIL_MOISTURE, linewidth=1.5, label="Độ ẩm đất (%)")
    ax2.set_ylabel("Độ ẩm đất (%)", color=COLOR_SOIL_MOISTURE)
    ax2.tick_params(axis="y", labelcolor=COLOR_SOIL_MOISTURE)

    fig.suptitle("So sánh Nhiệt độ và Độ ẩm đất theo thời gian", fontsize=14, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    fig.autofmt_xdate()
    _save_or_show(fig, save_path)


def plot_soil_moisture_histogram(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ Histogram phân bố Soil Moisture."""
    fig, ax = plt.subplots()
    ax.hist(df["soil_moisture"], bins=25, color=COLOR_SOIL_MOISTURE, edgecolor="white", alpha=0.85)
    ax.set_title("Phân bố Độ ẩm đất (Histogram)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Độ ẩm đất (%)")
    ax.set_ylabel("Tần suất")
    _save_or_show(fig, save_path)


def plot_soil_moisture_boxplot(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ Boxplot Soil Moisture để quan sát phân bố và outlier."""
    fig, ax = plt.subplots(figsize=(5, 6))
    box = ax.boxplot(
        df["soil_moisture"].dropna(),
        patch_artist=True,
        widths=0.4,
        tick_labels=["Độ ẩm đất"],
    )
    for patch in box["boxes"]:
        patch.set_facecolor(COLOR_SOIL_MOISTURE)
        patch.set_alpha(0.7)
    ax.set_title("Boxplot Độ ẩm đất", fontsize=14, fontweight="bold")
    ax.set_ylabel("Độ ẩm đất (%)")
    _save_or_show(fig, save_path)


def plot_correlation_heatmap(corr: pd.DataFrame, save_path: str | None = None) -> None:
    """Vẽ Correlation Heatmap bằng matplotlib thuần (không bắt buộc seaborn).

    Ghi chú: Nếu muốn dùng seaborn, thay bằng:
        import seaborn as sns
        sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    """
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)

    # Ghi giá trị số lên từng ô của heatmap.
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(
                j, i, f"{corr.iloc[i, j]:.2f}",
                ha="center", va="center",
                color="white" if abs(corr.iloc[i, j]) > 0.5 else "black",
                fontsize=9,
            )

    ax.set_title("Ma trận tương quan giữa các biến cảm biến", fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Hệ số tương quan")
    _save_or_show(fig, save_path)


def generate_all_charts(df: pd.DataFrame, corr: pd.DataFrame, output_dir: str = "../images") -> None:
    """Sinh toàn bộ 7 biểu đồ yêu cầu và lưu vào thư mục output_dir."""
    plot_temperature_over_time(df, f"{output_dir}/01_temperature_over_time.png")
    plot_soil_moisture_over_time(df, f"{output_dir}/02_soil_moisture_over_time.png")
    plot_humidity_over_time(df, f"{output_dir}/03_humidity_over_time.png")
    plot_temperature_vs_soil_moisture(df, f"{output_dir}/04_temperature_vs_soil_moisture.png")
    plot_soil_moisture_histogram(df, f"{output_dir}/05_soil_moisture_histogram.png")
    plot_soil_moisture_boxplot(df, f"{output_dir}/06_soil_moisture_boxplot.png")
    plot_correlation_heatmap(corr, f"{output_dir}/07_correlation_heatmap.png")
    print("[visualization.py] Đã sinh xong toàn bộ 7 biểu đồ.")


if __name__ == "__main__":
    from analysis import compute_correlation_matrix

    df = pd.read_csv("../data/simulated_data.csv", parse_dates=["created_at"])
    corr = compute_correlation_matrix(df)
    generate_all_charts(df, corr, output_dir="../images")
