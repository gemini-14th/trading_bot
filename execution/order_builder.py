from dataclasses import dataclass
from typing import Literal


@dataclass
class TradeOrder:
    instrument: str
    side: Literal["buy", "sell"]
    order_type: Literal["market"]
    units: int
    stop_loss: float
    take_profit: float
    comment: str = "AUTO_STRATEGY"


class OrderBuilder:
    """
    Builds broker-agnostic trade orders from analysis output
    """

    @staticmethod
    def build_from_analysis(analysis: dict) -> TradeOrder:
        side = "sell" if analysis["signal"] == "SELL" else "buy"

        units = int(analysis["position_size"])

        instrument = analysis["symbol"].replace("/", "_")

        return TradeOrder(
            instrument=instrument,
            side=side,
            order_type="market",
            units=units,
            stop_loss=analysis["stop_loss"],
            take_profit=analysis["take_profit"],
            comment=f"{analysis['signal']}_{analysis['trend']}"
        )
