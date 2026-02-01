from data.market_data_router import MarketDataRouter
from strategy.ema_rsi_strategy import EMARsiStrategy
from analytics.trend_engine import TrendEngine
from analytics.volatility import calculate_volatility, calculate_atr
from analytics.confidence_score import calculate_confidence
from analytics.recheck_engine import RecheckDecisionEngine
from analytics.signal_validator import SignalValidator
from analytics.signal_ranker import SignalRanker
from data.validators import validate_trade
from analytics.session_engine import MarketSessionEngine
from analytics.news_engine import NewsEngine

from risk.position_sizer import PositionSizer


# ==============================
# ENGINES
# ==============================

data_router = MarketDataRouter()
strategy = EMARsiStrategy()
trend_engine = TrendEngine()


# ==============================
# EXECUTION COST MODEL
# ==============================

def estimate_spread(symbol: str) -> float:
    """
    Approx Exness Standard spreads (pips)
    """
    spreads = {
        "EURUSD": 1.0,
        "GBPUSD": 1.4,
        "USDJPY": 1.2,
        "XAUUSD": 2.5
    }

    return spreads.get(symbol.upper(), 1.5)


# ==============================
# LIQUIDITY MODEL
# ==============================

def detect_liquidity_trap(df):

    recent = df.tail(12)

    high_break = recent.high.iloc[-1] > recent.high[:-1].max()
    low_break = recent.low.iloc[-1] < recent.low[:-1].min()

    close_inside = (
        recent.low[:-1].min()
        < recent.close.iloc[-1]
        < recent.high[:-1].max()
    )

    return {
        "buy_stop_hunt": bool(high_break and close_inside),
        "sell_stop_hunt": bool(low_break and close_inside)
    }


# ==============================
# PIP UTILS
# ==============================

def get_pip_size(symbol):

    symbol = symbol.upper()

    if "JPY" in symbol:
        return 0.01

    if "XAU" in symbol:
        return 0.1

    return 0.0001


# ==============================
# MAIN ENGINE
# ==============================

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
    PROFESSIONAL ANALYSIS ENGINE
    - Spread aware
    - Liquidity filtered
    - Risk controlled
    - Backtest safe
    """
    
    # ==============================
    # SESSION / NEWS FILTER

    session = MarketSessionEngine.market_status()

    if session["weekend"]:
        return {
            "market_open": False,
            "message": "Market closed (Weekend)",
            "session": session,
            "analysis_only": True
        }

    if not session["active_sessions"]:
        return {
            "market_open": False,
            "message": "No active trading session",
            "session": session,
            "analysis_only": True
        }

    if NewsEngine.is_news_time():

        return {
            "market_open": False,
            "message": "High impact news window",
            "session": session,
            "analysis_only": True
        }

        # ==============================
        # MARKET DATA

    try:
        df = data_router.fetch_ohlcv(symbol, interval)
    except Exception as e:
        return {"error": f"Market data failed: {e}"}

    if df is None or len(df) < 60:
        return {
            "market_open": False,
            "message": "Insufficient data"
        }


        # ==============================
        # STRATEGY

    try:
        signal = strategy.generate_signal(df)
        trend = trend_engine.classify_trend(df)
        entry = float(df.close.iloc[-1])
    except Exception as e:
        return {"error": f"Strategy failure: {e}"}


    rsi = float(getattr(strategy, "last_rsi", 50))
    ema_slope = float(getattr(strategy, "ema_slope", 0))


    stop = None
    take_profit = None
    sizing = None

    trade_allowed = False
    rr_ratio = None
    atr = None
    block_reason = None


    # ==============================
    # COST & LIQUIDITY
    # ==============================

    spread_pips = estimate_spread(symbol)

    liquidity = detect_liquidity_trap(df)


    # ==============================
    # TRADE LOGIC
    # ==============================

    if signal in ("BUY", "SELL"):

        # ------------------
        # ATR / VOLATILITY
        # ------------------

        try:
            atr = float(calculate_atr(df, 14))
            volatility = float(calculate_volatility(df))
        except Exception:
            atr = None
            volatility = None


        if not atr or atr <= 0:
            return {"error": "Invalid ATR"}


        SL_MULT = 1.5
        TP_MULT = 3.0


        if signal == "BUY":
            stop = entry - atr * SL_MULT
            take_profit = entry + atr * TP_MULT

        else:
            stop = entry + atr * SL_MULT
            take_profit = entry - atr * TP_MULT


        # ------------------
        # SL DISTANCE FILTER
        # ------------------

        pip_size = get_pip_size(symbol)

        sl_pips = abs(entry - stop) / pip_size


        if sl_pips < 10:
            block_reason = "SL_TOO_SMALL"
            signal = "HOLD"


        # ------------------
        # SPREAD FILTER
        # ------------------

        if spread_pips > sl_pips * 0.25:
            block_reason = "SPREAD_TOO_HIGH"
            signal = "HOLD"


        # ------------------
        # LIQUIDITY FILTER
        # ------------------

        if signal == "BUY" and liquidity["buy_stop_hunt"]:
            block_reason = "BUY_STOP_HUNT"
            signal = "HOLD"

        if signal == "SELL" and liquidity["sell_stop_hunt"]:
            block_reason = "SELL_STOP_HUNT"
            signal = "HOLD"


        # ------------------
        # STRUCTURE CHECK
        # ------------------

        if signal in ("BUY", "SELL"):

            trade_allowed = validate_trade(
                signal=signal,
                trend=trend,
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit
            )


        # ------------------
        # POSITION SIZING
        # ------------------

        if trade_allowed:

            try:

                if lot_size:

                    sizing = PositionSizer.calculate_from_lot(
                        symbol,
                        account_balance,
                        lot_size,
                        entry,
                        stop
                    )

                else:

                    sizing = PositionSizer.calculate_position(
                        symbol,
                        account_balance,
                        risk_percent,
                        entry,
                        stop
                    )

            except Exception:
                sizing = None


            if not sizing:
                trade_allowed = False
                block_reason = "SIZING_FAILED"


            else:

                if sizing["lots"] < min_lot:
                    trade_allowed = False
                    block_reason = "LOT_TOO_SMALL"

                if sizing["lots"] > max_lot:
                    sizing["lots"] = max_lot


                rr_ratio = abs(take_profit - entry) / abs(entry - stop)


        # ------------------
        # QUALITY FILTER
        # ------------------

        if trade_allowed:

            if rr_ratio < 2.0:
                trade_allowed = False
                block_reason = "LOW_RR"


            confidence = calculate_confidence(
                structure_score=0.7,
                indicator_score=0.8,
                volume_score=0.6,
                volatility_score=0.7
            )


            if confidence and confidence < 60:
                trade_allowed = False
                block_reason = "LOW_CONFIDENCE"


        # ==============================
        # RECHECK ENGINE
    # ==============================

    recheck = None

    if not trade_allowed:

        try:

            state = RecheckDecisionEngine.determine_state(
                signal=signal,
                trend=trend,
                rsi=rsi,
                volatility=volatility,
                ema_slope=ema_slope
            )

            recheck = RecheckDecisionEngine.build_recheck_response(
                state,
                interval
            )

        except Exception:
            recheck = None


        # ==============================
        # FINAL RESPONSE
    # ==============================

    return {
        "symbol": symbol,
        "interval": interval,

        "signal": signal,
        "trend": trend,

        "entry": round(entry, 5),

        "stop_loss": round(stop, 5) if stop else None,
        "take_profit": round(take_profit, 5) if take_profit else None,

        "atr": round(atr, 5) if atr else None,
        "volatility": round(volatility, 5) if volatility else None,

        "spread_pips": spread_pips,
        "liquidity": liquidity,

        "rr_ratio": round(rr_ratio, 2) if rr_ratio else None,

        "trade_allowed": trade_allowed,
        "block_reason": block_reason,

        "sizing": sizing,
        "recheck": recheck,

        "analysis_only": True
    }
