class RiskManager:
    """
    Risk Management Engine
    Responsibilities:
    - Capital preservation
    - Consistent position sizing
    """

    def calculate_position_size(
        self,
        account_balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """
        Position Size = (Account Balance × Risk %) / Stop Loss Distance
        """

        risk_amount = account_balance * risk_percent
        stop_distance = abs(entry_price - stop_loss_price)

        if stop_distance <= 0:
            return 0.0

        position_size = risk_amount / stop_distance
        return round(position_size, 4)
