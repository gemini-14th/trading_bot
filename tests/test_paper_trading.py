from data.market_data import MarketDataClient
from strategy.ema_rsi_strategy import EMARsiStrategy
from risk.position_sizing import RiskManager
from data.validators import validate_trade
from execution.paper_trader import PaperTrader


def main():
    client = MarketDataClient("https://api.binance.com/api/v3/klines")
    strategy = EMARsiStrategy()
    risk_manager = RiskManager()

    trader = PaperTrader(
        data_client=client,
        strategy=strategy,
        risk_manager=risk_manager,
        validator=validate_trade
    )

    trader.run_once()

    print("Paper Trade Log:", trader.trade_log)


if __name__ == "__main__":
    main()
