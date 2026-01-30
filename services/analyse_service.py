from data.market_data_router import MarketDataRouter
from strategy.ema_rsi_strategy import EMARsiStrategy
from analytics.trend_engine import TrendEngine
from analytics.volatility import calculate_volatility, calculate_atr
from analytics.confidence_score import calculate_confidence
from analytics.recheck_engine import RecheckDecisionEngine
from analytics.signal_validator import SignalValidator
from analytics.signal_ranker import SignalRanker
from data.validators import validate_trade

from risk.position_sizer import PositionSizer


# ==============================
# ENGINES (singletons)
# ==============================
data_router = MarketDataRouter()
strategy = EMARsiStrategy()
trend_engine = TrendEngine()


def analyze_market(
    *,
    symbol: str,
    interval: str,
    account_balance: float,
    risk_percent: float,
    lot_size: float | None,
    min_lot: float,
    max_lot: float
) -> dict:
    """
    ANALYSIS-ONLY ENGINE
    - ATR-based SL/TP
    - Risk-based position sizing
    - NO signal sending
    - NO caching
    """

    # ------------------
    # MARKET DATA
    # ------------------
    try:
        df = data_router.fetch_ohlcv(symbol, interval)
    except Exception:
        return {"error": f"Failed to fetch market data for {symbol} ({interval})"}

    if df is None or len(df) < 20:
        return {
            "market_open": False,
            "message": "Insufficient market data",
            "symbol": symbol,
            "interval": interval
        }

    # ------------------
    # STRATEGY & TREND
    # ------------------
    try:
        signal = strategy.generate_signal(df)
    except Exception:
        return {"error": "Failed to generate trading signal"}

    try:
        trend = trend_engine.classify_trend(df)
    except Exception:
        return {"error": "Failed to classify market trend"}

    try:
        entry = float(df.close.iloc[-1])
    except Exception:
        return {"error": "Failed to determine entry price"}

    rsi_value = getattr(strategy, "last_rsi", 50.0)
    ema_slope = getattr(strategy, "ema_slope", 0.0)

    stop = take_profit = None
    sizing = None
    trade_allowed = False
    lot_mode = "auto"
    rr_ratio = None
    atr = None

    # ------------------
    # TRADE LOGIC
    # ------------------
    if signal in ("BUY", "SELL"):

        # ==============================
        # ATR-BASED SL / TP
        # ==============================
        try:
            atr = calculate_atr(df, period=14)
        except Exception:
            return {"error": "Failed to calculate ATR"}

        SL_ATR_MULTIPLIER = 1.5
        TP_ATR_MULTIPLIER = 3.0

        if signal == "BUY":
            stop = entry - (atr * SL_ATR_MULTIPLIER)
            take_profit = entry + (atr * TP_ATR_MULTIPLIER)
        else:
            stop = entry + (atr * SL_ATR_MULTIPLIER)
            take_profit = entry - (atr * TP_ATR_MULTIPLIER)

        # ------------------
        # VALIDATE TRADE STRUCTURE
        # ------------------
        try:
            trade_allowed = validate_trade(
                signal=signal,
                trend=trend,
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit
            )
        except Exception:
            trade_allowed = False

        # ------------------
        # POSITION SIZING
        # ------------------
        if trade_allowed:
            if lot_size is not None:
                try:
                    sizing = PositionSizer.calculate_from_lot(
                        symbol=symbol,
                        balance=account_balance,
                        lot_size=lot_size,
                        entry_price=entry,
                        stop_loss=stop
                    )
                    lot_mode = "manual"
                except Exception:
                    sizing = None
            else:
                try:
                    sizing = PositionSizer.calculate_position(
                        symbol=symbol,
                        balance=account_balance,
                        risk_percent=risk_percent,
                        entry_price=entry,
                        stop_loss=stop
                    )

                    if sizing and sizing["lots"] < min_lot:
                        trade_allowed = False

                except Exception:
                    sizing = None

            if sizing:
                rr_ratio = abs(take_profit - entry) / abs(entry - stop)

    # ------------------
    # ANALYTICS
    # ------------------
    try:
        volatility = calculate_volatility(df)
    except Exception:
        volatility = None

    try:
        confidence = calculate_confidence(
            structure_score=0.7,
            indicator_score=0.8,
            volume_score=0.6,
            volatility_score=0.7
        )
    except Exception:
        confidence = None

    # ------------------
    # RECHECK ENGINE
    # ------------------
    recheck_advice = None
    if not trade_allowed:
        try:
            state = RecheckDecisionEngine.determine_state(
                signal=signal,
                trend=trend,
                rsi=rsi_value,
                volatility=volatility,
                ema_slope=ema_slope
            )
            recheck_advice = RecheckDecisionEngine.build_recheck_response(
                state=state,
                timeframe=interval
            )
        except Exception:
            pass

    # ------------------
    # SIGNAL QUALITY CHECK
    # ------------------
    valid = False
    highlighted = False
    signal_payload = None

    if trade_allowed and sizing:
        signal_payload = {
            "symbol": symbol,
            "signal": signal,
            "interval": interval,
            "entry_price": entry,
            "stop_loss": stop,
            "take_profit": take_profit,
            "confidence_percent": confidence,
            "lot_size": sizing["lots"],
            "rr_ratio": round(rr_ratio, 2) if rr_ratio else None,
            "volatility": volatility,
            "atr": round(atr, 5) if atr else None
        }

        valid, _ = SignalValidator.validate(signal_payload)
        highlighted = SignalRanker.is_high_profit(signal_payload)

    # ------------------
    # RETURN PURE ANALYSIS
    # ------------------
    return {
        "symbol": symbol,
        "interval": interval,
        "signal": signal,
        "trend": trend,
        "entry_price": round(entry, 4),
        "stop_loss": round(stop, 4) if stop else None,
        "take_profit": round(take_profit, 4) if take_profit else None,
        "atr": round(atr, 5) if atr else None,
        "volatility": volatility,
        "confidence_percent": confidence,
        "trade_allowed": trade_allowed,
        "risk_percent": risk_percent,
        "lot_mode": lot_mode,
        "sizing": sizing,
        "rr_ratio": round(rr_ratio, 2) if rr_ratio else None,
        "recheck_advice": recheck_advice,
        "valid_signal": valid,
        "highly_profitable": highlighted,
        "analysis_only": True
    }