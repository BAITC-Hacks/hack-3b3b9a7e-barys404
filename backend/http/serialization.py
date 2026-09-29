import math
from datetime import date
from typing import Any

import numpy as np
import pandas as pd


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, pd.DataFrame):
        return [json_safe(row) for row in value.to_dict(orient="records")]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()[:10]
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value
