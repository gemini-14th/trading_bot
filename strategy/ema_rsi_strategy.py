import pandas as pd
from strategy.base_strategy import BaseStrategy


class EMARsiStrategy(BaseStrategy):
    """
    EMA + RSI strategy
    Rules:
    - EMA 50 > EMA 200 → Bullish bias
    - RSI > 50 → Momentum confirmation
    """

    def generate_signal(self, df: pd.DataFrame) -> str:
        df = df.copy()

        df["ema_fast"] = df["close"].ewm(span=50).mean()
        df["ema_slow"] = df["close"].ewm(span=200).mean()

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        last = df.iloc[-1]

        if last.ema_fast > last.ema_slow and last.rsi > 50:
            return "BUY"

        if last.ema_fast < last.ema_slow and last.rsi < 50:
            return "SELL"

        return "NO_TRADE"
