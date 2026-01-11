from data.market_data import MarketDataClient
from strategy.ema_rsi_strategy import EMARsiStrategy
from risk.position_sizing import RiskManager
from data.validators import validate_trade
from backtesting.backtester import Backtester
from backtesting.metrics import performance_report


def main():
    client = MarketDataClient("https://api.binance.com/api/v3/klines")
    df = client.fetch_ohlcv("BTCUSDT", "1h")

    strategy = EMARsiStrategy()
    risk_manager = RiskManager()

    backtester = Backtester(
        strategy=strategy,
        risk_manager=risk_manager,
        validator=validate_trade
    )

    trades = backtester.run(df)
    report = performance_report(trades)

    print("Backtest Trades:", len(trades))
    print("Performance Report:", report)


if __name__ == "__main__":
    main()
