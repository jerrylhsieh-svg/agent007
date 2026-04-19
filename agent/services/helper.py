import math
from typing import Any


def safe_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0
    
def thirty_days_avg(total_amount: float, total_days: int):
    return round(total_amount/total_days*30, 2)