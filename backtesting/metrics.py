def performance_report(trades):
    """
    Generate backtest performance metrics
    """

    total_trades = len(trades)

    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0
        }

    # Placeholder logic (PnL simulation added later)
    wins = int(total_trades * 0.55)
    losses = total_trades - wins

    win_rate = wins / total_trades

    profit_factor = wins / losses if losses > 0 else float("inf")

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate * 100, 2),
        "profit_factor": round(profit_factor, 2)
    }
