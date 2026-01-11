class PaperBroker:
    """
    Simulates trade execution without real money
    """

    def __init__(self, starting_balance: float = 10_000):
        self.balance = starting_balance
        self.open_trades = []

    def execute(self, order):
        trade = {
            "instrument": order.instrument,
            "side": order.side,
            "units": order.units,
            "stop_loss": order.stop_loss,
            "take_profit": order.take_profit,
            "status": "OPEN"
        }

        self.open_trades.append(trade)

        return {
            "message": "Paper trade executed",
            "trade": trade,
            "balance": self.balance
        }
