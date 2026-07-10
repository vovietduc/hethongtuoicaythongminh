"""
irrigation_logic.py
--------------------
Module thuật toán ra quyết định điều khiển máy bơm tưới cây.

Quy tắc điều khiển (rule-based, kết hợp kết quả từ prediction.py):
    1. Nếu Soil Moisture < 40%          -> Bật bơm (PUMP ON)
    2. Nếu Soil Moisture > 60%          -> Tắt bơm (PUMP OFF)
    3. Nếu 40% <= Soil Moisture <= 60%  -> Giữ nguyên trạng thái hiện tại
    4. Nếu Moving Average giảm liên tục -> Phát cảnh báo "sắp khô", dù bơm
       có thể chưa cần bật ngay theo ngưỡng.

Tác giả: Đồ án Hệ thống tưới cây thông minh ESP32 + ThingSpeak
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

LOW_THRESHOLD = 40.0   # Dưới ngưỡng này -> bắt buộc bật bơm
HIGH_THRESHOLD = 60.0  # Trên ngưỡng này -> bắt buộc tắt bơm


class PumpAction(str, Enum):
    """Các hành động có thể thực hiện với máy bơm."""

    ON = "PUMP_ON"
    OFF = "PUMP_OFF"
    HOLD = "HOLD_STATE"  # Giữ nguyên trạng thái hiện tại (vùng an toàn)


@dataclass
class IrrigationDecision:
    """Kết quả quyết định tưới tại một thời điểm."""

    action: PumpAction
    warning: bool          # Có cảnh báo "sắp khô" hay không
    reason: str             # Diễn giải lý do ra quyết định (tiếng Việt, dễ hiểu)


def decide_irrigation(
    soil_moisture: float,
    is_drying_trend: bool,
    current_pump_state: PumpAction = PumpAction.OFF,
    low_threshold: float = LOW_THRESHOLD,
    high_threshold: float = HIGH_THRESHOLD,
) -> IrrigationDecision:
    """Ra quyết định bật/tắt bơm dựa trên độ ẩm đất hiện tại và xu hướng.

    Tham số:
        soil_moisture: Giá trị độ ẩm đất hiện tại (%).
        is_drying_trend: Kết quả từ prediction.detect_drying_trend() — True nếu
            Moving Average đang giảm liên tục (đất sắp khô).
        current_pump_state: Trạng thái bơm hiện tại, dùng cho vùng an toàn (HOLD).
        low_threshold: Ngưỡng dưới (mặc định 40%).
        high_threshold: Ngưỡng trên (mặc định 60%).

    Trả về:
        IrrigationDecision gồm hành động, cờ cảnh báo và lý do.
    """
    if soil_moisture < low_threshold:
        action = PumpAction.ON
        reason = f"Độ ẩm đất ({soil_moisture:.1f}%) dưới ngưỡng {low_threshold}% -> cần tưới ngay."
    elif soil_moisture > high_threshold:
        action = PumpAction.OFF
        reason = f"Độ ẩm đất ({soil_moisture:.1f}%) trên ngưỡng {high_threshold}% -> đủ nước, tắt bơm."
    else:
        action = PumpAction.HOLD
        reason = (
            f"Độ ẩm đất ({soil_moisture:.1f}%) nằm trong vùng an toàn "
            f"[{low_threshold}%, {high_threshold}%] -> giữ nguyên trạng thái bơm ({current_pump_state.value})."
        )

    warning = is_drying_trend and action != PumpAction.ON
    if warning:
        reason += " CẢNH BÁO: xu hướng độ ẩm đang giảm liên tục, đất có nguy cơ sắp khô."

    return IrrigationDecision(action=action, warning=warning, reason=reason)


def run_decision_over_dataframe(
    df: pd.DataFrame,
    drying_flags: pd.Series | None = None,
) -> pd.DataFrame:
    """Áp dụng thuật toán quyết định cho toàn bộ DataFrame (mô phỏng theo từng dòng).

    Tham số:
        df: DataFrame có cột 'soil_moisture'.
        drying_flags: Series bool cùng độ dài với df, đánh dấu xu hướng khô tại mỗi dòng
            (nếu None, mặc định coi như không có xu hướng khô — chỉ dùng ngưỡng tĩnh).

    Trả về:
        DataFrame gốc kèm 2 cột mới: 'decision_action' và 'decision_warning'.
    """
    result = df.copy()
    current_state = PumpAction.OFF

    actions = []
    warnings = []

    for i in range(len(result)):
        moisture = result.loc[i, "soil_moisture"]
        drying = bool(drying_flags.iloc[i]) if drying_flags is not None else False

        decision = decide_irrigation(moisture, drying, current_state)
        if decision.action != PumpAction.HOLD:
            current_state = decision.action

        actions.append(decision.action.value)
        warnings.append(decision.warning)

    result["decision_action"] = actions
    result["decision_warning"] = warnings
    return result


if __name__ == "__main__":
    # Ví dụ minh họa nhanh 3 trường hợp.
    examples = [
        (35.0, False),
        (65.0, False),
        (50.0, True),
    ]
    for moisture, drying in examples:
        decision = decide_irrigation(moisture, drying)
        print(f"Soil Moisture={moisture}% | Drying={drying} -> {decision.action.value} | {decision.reason}")
