from data.market_data import MarketDataClient
from analytics.trend_engine import TrendEngine
from analytics.confidence_score import calculate_confidence
from analytics.volatility import calculate_volatility


def main():
    client = MarketDataClient("https://api.binance.com/api/v3/klines")
    df = client.fetch_ohlcv("BTCUSDT", "1h")

    trend_engine = TrendEngine()
    trend = trend_engine.classify_trend(df)

    volatility = calculate_volatility(df)

    confidence = calculate_confidence(
        structure_score=0.7,
        indicator_score=0.8,
        volume_score=0.6,
        volatility_score=0.7
    )

    print("Trend:", trend)
    print("Volatility:", volatility)
    print("Confidence %:", confidence)


if __name__ == "__main__":
    main()
