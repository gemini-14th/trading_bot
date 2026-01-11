from data.market_data import MarketDataClient


def main():
    client = MarketDataClient("https://api.binance.com/api/v3/klines")
    df = client.fetch_ohlcv("BTCUSDT", "1h")

    print(df.head())
    print("\nData fetched successfully!")


if __name__ == "__main__":
    main()
