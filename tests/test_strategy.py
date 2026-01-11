from data.market_data import MarketDataClient
from strategy.ema_rsi_strategy import EMARsiStrategy


def main():
    data_client = MarketDataClient("https://api.binance.com/api/v3/klines")
    strategy = EMARsiStrategy()

    df = data_client.fetch_ohlcv("BTCUSDT", "1h")
    signal = strategy.generate_signal(df)

    print("Strategy Signal:", signal)


if __name__ == "__main__":
    main()
