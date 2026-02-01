from enum import Enum


class MarketState(str, Enum):
    TREND_MISMATCH = "TREND_MISMATCH"
    RANGING = "RANGING"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    OVEREXTENDED = "OVEREXTENDED"
    PULLBACK_PENDING = "PULLBACK_PENDING"
    BREAKOUT_SETUP = "BREAKOUT_SETUP"
    CHOPPY_HIGH_VOL = "CHOPPY_HIGH_VOL"


# Timeframe to minutes
TIMEFRAME_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}


# How many candles to wait per state
STATE_TO_CANDLES = {
    MarketState.TREND_MISMATCH: 2,
    MarketState.RANGING: 3,
    MarketState.LOW_VOLATILITY: 4,
    MarketState.OVEREXTENDED: 2,
    MarketState.PULLBACK_PENDING: 1,
    MarketState.BREAKOUT_SETUP: 1,
    MarketState.CHOPPY_HIGH_VOL: 5,
}


class RecheckDecisionEngine:

    @staticmethod
    def determine_state(
        signal: str,
        trend: str,
        rsi: float | None,
        volatility: float | None,
        ema_slope: float | None,
        atr_threshold: float = 0.001
    ) -> MarketState:
        """
        Decide WHY a trade is not allowed.
        Defensive + trader-safe logic.
        """

        # ============================
        # 0️⃣ DATA VALIDATION (CRITICAL)
        # ============================

        if (
            volatility is None
            or ema_slope is None
            or rsi is None
        ):
            # No reliable data → stay out
            return MarketState.RANGING

        # ============================
        # 1️⃣ Choppy / High Volatility
        # ============================

        if (
            volatility > atr_threshold * 3
            and abs(ema_slope) < atr_threshold
        ):
            return MarketState.CHOPPY_HIGH_VOL

        # ============================
        # 2️⃣ Trend Mismatch
        # ============================

        if signal in ("BUY", "SELL"):

            if (
                (signal == "BUY" and trend != "Bullish") or
                (signal == "SELL" and trend != "Bearish")
            ):
                return MarketState.TREND_MISMATCH

        # ============================
        # 3️⃣ Low Volatility
        # ============================

        if volatility < atr_threshold:
            return MarketState.LOW_VOLATILITY

        # ============================
        # 4️⃣ Overextended Market
        # ============================

        if rsi >= 70 or rsi <= 30:
            return MarketState.OVEREXTENDED

        # ============================
        # 5️⃣ Pullback Pending
        # ============================

        if abs(ema_slope) > atr_threshold and signal == "NONE":
            return MarketState.PULLBACK_PENDING

        # ============================
        # 6️⃣ Default: Ranging
        # ============================

        return MarketState.RANGING

    # ==================================================
    # RESPONSE BUILDER
    # ==================================================

    @staticmethod
    def build_recheck_response(
        state: MarketState,
        timeframe: str
    ) -> dict:

        candles = STATE_TO_CANDLES.get(state, 3)
        minutes = candles * TIMEFRAME_MINUTES.get(timeframe, 60)

        return {
            "market_state": state.value,
            "recheck_after_candles": candles,
            "recheck_timeframe": timeframe,
            "estimated_wait_minutes": minutes,
            "next_check_hint": RecheckDecisionEngine._hint_for_state(state)
        }

    # ==================================================
    # HINT SYSTEM
    # ==================================================

    @staticmethod
    def _hint_for_state(state: MarketState) -> str:

        hints = {
            MarketState.TREND_MISMATCH:
                "Wait for trend and signal alignment",

            MarketState.RANGING:
                "Wait for breakout or volatility expansion",

            MarketState.LOW_VOLATILITY:
                "Wait for momentum or session open",

            MarketState.OVEREXTENDED:
                "Wait for pullback toward EMA",

            MarketState.PULLBACK_PENDING:
                "Recheck after next candle close",

            MarketState.BREAKOUT_SETUP:
                "Monitor closely at candle close",

            MarketState.CHOPPY_HIGH_VOL:
                "Let market stabilize before trading",
        }

        return hints.get(state, "Wait for clearer market structure")
