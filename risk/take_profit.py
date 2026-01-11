def fixed_rr_take_profit(
    entry_price: float,
    stop_loss_price: float,
    rr_ratio: float,
    direction: str
) -> float:
    """
    Fixed Risk:Reward take profit
    """

    risk = abs(entry_price - stop_loss_price)

    if direction == "BUY":
        return entry_price + (risk * rr_ratio)

    if direction == "SELL":
        return entry_price - (risk * rr_ratio)

    raise ValueError("Direction must be BUY or SELL")
