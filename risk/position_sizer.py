from dataclasses import dataclass


@dataclass
class InstrumentSpec:
    symbol: str
    pip_size: float
    pip_value_per_unit: float
    lot_size: int = 100_000  # standard lot


class PositionSizer:
    """
    Professional risk-based position sizing engine
    """

    DEFAULT_SPECS = {
    "EURUSD": InstrumentSpec(
        symbol="EURUSD",
        pip_size=0.0001,
        pip_value_per_unit=0.0001
    ),
    "GBPUSD": InstrumentSpec(
        symbol="GBPUSD",
        pip_size=0.0001,
        pip_value_per_unit=0.0001
    ),
    "USDJPY": InstrumentSpec(
        symbol="USDJPY",
        pip_size=0.01,
        pip_value_per_unit=0.0001
    ),
    "XAUUSD": InstrumentSpec(
        symbol="XAUUSD",
        pip_size=0.01,
        pip_value_per_unit=0.01,
        lot_size=100
    ),
}

    @classmethod
    def calculate_position(
        cls,
        symbol: str,
        balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss: float
    ) -> dict:
        """
        Returns units, lots, risk_amount, pip_distance
        """

        clean_symbol = symbol.replace("/", "")
        if clean_symbol not in cls.DEFAULT_SPECS:
            raise ValueError(f"No instrument spec for {symbol}")

        spec = cls.DEFAULT_SPECS[clean_symbol]

        risk_amount = balance * (risk_percent / 100)

        pip_distance = abs(entry_price - stop_loss) / spec.pip_size

        if pip_distance <= 0:
            raise ValueError("Invalid stop loss distance")

        units = risk_amount / (pip_distance * spec.pip_value_per_unit)
        lots = units / spec.lot_size

        return {
            "units": round(units, 2),
            "lots": round(lots, 3),
            "risk_amount": round(risk_amount, 2),
            "pip_distance": round(pip_distance, 1)
        }
