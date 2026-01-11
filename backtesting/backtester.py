class Backtester:
    """
    Backtesting Engine
    Simulates strategy performance on historical data
    """

    def __init__(self, strategy, risk_manager, validator):
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.validator = validator
        self.trades = []

    def run(self, df, balance=10000, risk_pct=0.01):
        """
        Run backtest candle-by-candle
        """

        for i in range(200, len(df)):
            window = df.iloc[:i]
            signal = self.strategy.generate_signal(window)

            if signal == "NO_TRADE":
                continue

            entry = window.close.iloc[-1]
            direction = signal

            stop = entry * (0.99 if direction == "BUY" else 1.01)
            take_profit = entry + (entry - stop) * 2 if direction == "BUY" else entry - (stop - entry) * 2

            valid = self.validator(
                signal=signal,
                trend="Bullish",  # HTF trend placeholder
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit
            )

            if not valid:
                continue

            size = self.risk_manager.calculate_position_size(
                balance, risk_pct, entry, stop
            )

            self.trades.append({
                "signal": signal,
                "entry": entry,
                "stop": stop,
                "take_profit": take_profit,
                "size": size
            })

        return self.trades
