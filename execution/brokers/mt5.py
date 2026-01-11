class MT5Bridge:
    """
    Generates MT5-compatible trade instructions
    """

    @staticmethod
    def generate(order):
        lots = round(order.units / 100_000, 2)

        return {
            "symbol": order.instrument.replace("_", ""),
            "action": order.side.upper(),
            "volume_lots": lots,
            "order_type": "MARKET",
            "stop_loss": order.stop_loss,
            "take_profit": order.take_profit,
            "comment": order.comment
        }
