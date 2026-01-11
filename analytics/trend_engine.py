import pandas as pd


class TrendEngine:
    """
    Trend & Analytics Engine
    Purpose:
    - Determine market bias
    - Not prediction, only classification
    """

    def classify_trend(self, df: pd.DataFrame) -> str:
        """
        Trend logic:
        - Price above MA → Bullish
        - Price below MA → Bearish
        - Otherwise → Ranging
        """

        df = df.copy()
        df["ma_50"] = df["close"].rolling(50).mean()

        last_price = df["close"].iloc[-1]
        last_ma = df["ma_50"].iloc[-1]

        if last_price > last_ma:
            return "Bullish"

        if last_price < last_ma:
            return "Bearish"

        return "Ranging"
