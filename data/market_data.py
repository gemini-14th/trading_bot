import requests
import pandas as pd


class MarketDataClient:
    """
    Market Data Engine
    Responsibilities:
    - Fetch OHLCV data
    - Normalize structure
    - Validate data integrity
    """

    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_ohlcv(self, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
        """
        Fetch OHLCV data from exchange API
        """

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        response = requests.get(self.base_url, params=params, timeout=5)
        response.raise_for_status()

        raw_data = response.json()

        df = pd.DataFrame(
            raw_data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "ignore"
            ]
        )

        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df[["open", "high", "low", "close", "volume"]] = df[
            ["open", "high", "low", "close", "volume"]
        ].astype(float)

        return df

