def fixed_percentage_stop(entry_price: float, percent: float, direction: str) -> float:
    """
    Fixed percentage stop-loss
    """

    if direction == "BUY":
        return entry_price * (1 - percent)

    if direction == "SELL":
        return entry_price * (1 + percent)

    raise ValueError("Direction must be BUY or SELL")
