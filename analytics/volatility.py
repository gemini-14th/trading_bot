import pandas as pd
import numpy as np


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Average True Range (ATR)
    Measures market volatility
    """

    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)

    tr = np.maximum(
        high - low,
        np.maximum(
            abs(high - prev_close),
            abs(low - prev_close)
        )
    )

    atr = tr.rolling(period).mean()

    return float(atr.iloc[-1])


def calculate_volatility(df: pd.DataFrame) -> float:
    """
    Normalized volatility score (0–1)
    Used for confidence + analytics
    """

    returns = df["close"].pct_change()
    volatility = returns.std()

    # Normalize to 0–1 range
    return round(min(volatility * 100, 1.0), 3)
