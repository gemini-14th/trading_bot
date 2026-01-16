# analytics/auto_signal_scanner.py

from analytics.signal_scoring import SignalScoringEngine
from analytics.signal_dispatcher import SignalDispatcher
from services.analyse_service import analyze_market


class AutoSignalScanner:
    """
    Scans symbols and sends WhatsApp signals if valid.
    """

    SYMBOLS = [
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "XAU/USD",
        "BTC/USD"
    ]

    @staticmethod
    def scan_and_dispatch(
        interval: str,
        account_balance: float,
        risk_percent: float
    ):


        for symbol in AutoSignalScanner.SYMBOLS:
            try:
                result = analyze_market(
                    symbol=symbol,
                    interval=interval,
                    account_balance=account_balance,
                    risk_percent=risk_percent,
                    lot_size=None
                )

                if not result.get("trade_allowed"):
                    continue

                scored = SignalScoringEngine.score(result)

                # 🚨 Only send meaningful signals
                if scored["confidence_percent"] < 65:
                    continue

                SignalDispatcher.send(
                    signal=scored,
                    highlighted=scored["highlighted"]
                )

            except Exception as e:
                print(f"[AutoSignalScanner] Error for {symbol}: {e}")