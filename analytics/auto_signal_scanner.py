from services.analyse_service import analyze_market
from analytics.signal_validator import SignalValidator
from analytics.signal_ranker import SignalRanker
from analytics.signal_dispatcher import SignalDispatcher

class AutoSignalScanner:

    SYMBOLS = [
        "EURUSD", "GBPUSD", "USDJPY",
        "AUDUSD", "USDCAD", "XAGUSD",
        "XAUUSD", "BTCUSDT", "XPTUSD"
    ]

    @classmethod
    def scan_and_dispatch(cls, interval, account_balance, risk_percent):
        valid_signals = []

        for symbol in cls.SYMBOLS:
            try:
                result = analyze_market(
                    symbol=symbol,
                    interval=interval,
                    account_balance=account_balance,
                    risk_percent=risk_percent,
                    lot_size=None,
                    min_lot=0.001,
                    max_lot=100
                )

                if SignalValidator.is_valid(result):
                    valid_signals.append(result)

            except Exception as e:
                print(f"[SCAN ERROR] {symbol}: {e}")

        if not valid_signals:
            print("No valid signals found")
            return

        ranked = SignalRanker.rank(valid_signals)

        # Send only top 3 strongest signals
        for signal in ranked[:3]:
            SignalDispatcher.dispatch(signal)
