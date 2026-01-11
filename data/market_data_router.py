from data.market_data import MarketDataClient
from data.twelve_data_market_data import TwelveDataMarketDataClient


class MarketDataRouter:
    """
    Routes symbols to the correct market data provider
    """

    def __init__(self):
        self.crypto_client = MarketDataClient(
            "https://api.binance.com/api/v3/klines"
        )
        self.multi_asset_client = TwelveDataMarketDataClient()

    def fetch_ohlcv(self, symbol: str, interval: str):
        # Crypto via Binance
        if symbol.endswith("USDT"):
            return self.crypto_client.fetch_ohlcv(symbol, interval)

        # Forex / Stocks / Indices via Twelve Data
        return self.multi_asset_client.fetch_ohlcv(symbol, interval)
