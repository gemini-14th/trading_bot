import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class TwelveDataMarketDataClient:
    """
    Twelve Data Market Data Client
    Supports Forex, Crypto, Stocks
    """

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self):
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")

        if not self.api_key:
            raise ValueError("TWELVE_DATA_API_KEY not found in environment")

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        outputsize: int = 500
    ) -> pd.DataFrame:
        normalized_symbol = (
            symbol if "/" in symbol else f"{symbol[:3]}/{symbol[3:]}"
        )


        interval_map = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1day"
}

        interval = interval_map.get(interval, interval)

        params = {
            "symbol": normalized_symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key,
            "format": "JSON"
        }

        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "status" in data and data["status"] == "error":
            raise ValueError(f"Twelve Data error: {data.get('message')}")


        values = data.get("values")
        if not values:
            raise ValueError("No data returned from Twelve Data")

        df = pd.DataFrame(values)
        df = df.rename(columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        })

        # Convert OHLC to float
        df[["open", "high", "low", "close"]] = df[
            ["open", "high", "low", "close"]
        ].astype(float)

        # Volume is not available for Forex → fill with 0
        if "volume" in df.columns:
            df["volume"] = df["volume"].astype(float)
        else:
            df["volume"] = 0.0

        df = df.iloc[::-1].reset_index(drop=True)
        return df
