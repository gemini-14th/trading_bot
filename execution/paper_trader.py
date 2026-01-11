import time


class PaperTrader:
    """
    Paper Trading Engine
    Simulates live trading with virtual capital
    """

    def __init__(
        self,
        data_client,
        strategy,
        risk_manager,
        validator,
        starting_balance=10000
    ):
        self.data_client = data_client
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.validator = validator

        self.balance = starting_balance
        self.open_position = None
        self.trade_log = []

    def run_once(self, symbol="BTCUSDT", interval="1h", risk_pct=0.01):
        """
        Execute one paper trading cycle
        """

        df = self.data_client.fetch_ohlcv(symbol, interval)
        signal = self.strategy.generate_signal(df)

        if signal == "NO_TRADE" or self.open_position:
            return

        entry = df.close.iloc[-1]
        direction = signal

        stop = entry * (0.99 if direction == "BUY" else 1.01)
        take_profit = (
            entry + (entry - stop) * 2
            if direction == "BUY"
            else entry - (stop - entry) * 2
        )

        valid = self.validator(
            signal=signal,
            trend="Bullish",
            entry=entry,
            stop_loss=stop,
            take_profit=take_profit
        )

        if not valid:
            return

        size = self.risk_manager.calculate_position_size(
            self.balance, risk_pct, entry, stop
        )

        self.open_position = {
            "signal": signal,
            "entry": entry,
            "stop": stop,
            "take_profit": take_profit,
            "size": size
        }

        self.trade_log.append(self.open_position)
        print("📄 Paper Trade Opened:", self.open_position)
