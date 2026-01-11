def validate_trade(
    signal: str,
    trend: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    min_rr: float = 2.0
) -> bool:
    """
    Trade validation rules
    """

    if signal == "NO_TRADE":
        return False

    # Counter-trend filter
    if signal == "BUY" and trend == "Bearish":
        return False

    if signal == "SELL" and trend == "Bullish":
        return False

    # Risk-Reward check
    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)

    if risk == 0:
        return False

    rr = reward / risk
    if rr < min_rr:
        return False

    return True
