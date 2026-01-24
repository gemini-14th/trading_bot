# analytics/signal_scoring.py

class SignalScoringEngine:
    """
    Scores trade signals to decide if they are normal or high-profit.
    """

    @staticmethod
    def score(signal: dict) -> dict:
        confidence = signal.get("confidence_percent", 0)
        entry = signal.get("entry_price")
        stop = signal.get("stop_loss")
        tp = signal.get("take_profit")

        rr_ratio = None
        if entry and stop and tp:
            risk = abs(entry - stop)
            reward = abs(tp - entry)
            if risk > 0:
                rr_ratio = round(reward / risk, 2)

        signal["rr_ratio"] = rr_ratio

        highlighted = (
            confidence >= 80 and
            rr_ratio is not None and
            rr_ratio >= 2.5
        )

        signal["highlighted"] = highlighted
        return signal