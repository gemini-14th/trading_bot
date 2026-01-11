import pandas as pd


def calculate_volatility(df: pd.DataFrame, period: int = 14) -> float:
    """
    Simple volatility estimation using high-low range
    """

    df = df.copy()
    df["range"] = df["high"] - df["low"]

    volatility = df["range"].rolling(period).mean().iloc[-1]
    return round(volatility, 4)
