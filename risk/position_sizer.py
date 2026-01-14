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
    Supports:
    - Auto sizing from account balance & risk %
    - Manual lot sizing with real risk calculation
    """

    MIN_LOT = 0.001
    MAX_LOT = 100.0

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

    # ==============================
    # AUTO SAFE MODE (RECOMMENDED)
    # ==============================
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
        Calculates SAFE lot size based on account balance and risk %
        """

        clean_symbol = symbol.replace("/", "").upper()
        if clean_symbol not in cls.DEFAULT_SPECS:
            raise ValueError(f"No instrument spec for {symbol}")

        spec = cls.DEFAULT_SPECS[clean_symbol]

        risk_amount = balance * (risk_percent / 100)

        pip_distance = abs(entry_price - stop_loss) / spec.pip_size
        if pip_distance <= 0:
            raise ValueError("Invalid stop loss distance")

        units = risk_amount / (pip_distance * spec.pip_value_per_unit)
        lots = units / spec.lot_size

        # ------------------
        # SAFETY CLAMPS
        # ------------------
        lots = max(cls.MIN_LOT, min(lots, cls.MAX_LOT))
        units = lots * spec.lot_size

        return {
            "units": round(units, 2),
            "lots": round(lots, 4),
            "units_per_lot": spec.lot_size,
            "risk_amount": round(risk_amount, 2),
            "pip_distance": round(pip_distance, 1),
            "actual_risk_percent": round(risk_percent, 2)
        }

    # ==============================
    # MANUAL LOT MODE (ADVANCED)
    # ==============================
    @classmethod
    def calculate_from_lot(
        cls,
        symbol: str,
        balance: float,
        lot_size: float,
        entry_price: float,
        stop_loss: float
    ) -> dict:
        """
        Calculates ACTUAL risk when user chooses lot size manually
        """

        if not (cls.MIN_LOT <= lot_size <= cls.MAX_LOT):
            raise ValueError(
                f"Lot size must be between {cls.MIN_LOT} and {cls.MAX_LOT}"
            )

        clean_symbol = symbol.replace("/", "").upper()
        if clean_symbol not in cls.DEFAULT_SPECS:
            raise ValueError(f"No instrument spec for {symbol}")

        spec = cls.DEFAULT_SPECS[clean_symbol]

        pip_distance = abs(entry_price - stop_loss) / spec.pip_size
        if pip_distance <= 0:
            raise ValueError("Invalid stop loss distance")

        units = lot_size * spec.lot_size
        risk_amount = pip_distance * units * spec.pip_value_per_unit
        actual_risk_percent = (risk_amount / balance) * 100

        return {
            "units": round(units, 2),
            "lots": round(lot_size, 4),
            "units_per_lot": spec.lot_size,
            "risk_amount": round(risk_amount, 2),
            "pip_distance": round(pip_distance, 1),
            "actual_risk_percent": round(actual_risk_percent, 2)
        }
