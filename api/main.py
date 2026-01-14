from fastapi import FastAPI, Query

from data.market_data_router import MarketDataRouter
from strategy.ema_rsi_strategy import EMARsiStrategy
from risk.stop_loss import fixed_percentage_stop
from risk.take_profit import fixed_rr_take_profit
from risk.position_sizer import PositionSizer
from analytics.trend_engine import TrendEngine
from analytics.volatility import calculate_volatility
from analytics.confidence_score import calculate_confidence
from analytics.recheck_engine import RecheckDecisionEngine
from data.validators import validate_trade

from execution.order_builder import OrderBuilder
from execution.brokers.paper import PaperBroker
from execution.brokers.mt5 import MT5Bridge
from notifications.recheck_scheduler import schedule_recheck


app = FastAPI(title="Trading Analysis Chatbot")

# ==============================
# CONFIG
# ==============================
ACCOUNT_BALANCE = 100_000

MIN_RISK_PERCENT = 0.1
MAX_RISK_PERCENT = 10.0
DEFAULT_RISK = 1.0

MIN_LOT_SIZE = 0.001
MAX_LOT_SIZE = 100.0

# ==============================
# ENGINES
# ==============================
data_router = MarketDataRouter()
strategy = EMARsiStrategy()
trend_engine = TrendEngine()
paper_broker = PaperBroker()

# ==============================
# HEALTH
# ==============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ==============================
# ANALYZE
# ==============================
@app.get("/analyze")
def analyze(
    symbol: str,
    interval: str = "1h",
    risk_percent: float = DEFAULT_RISK,
    max_lot_size: float | None = None
):
    # ------------------
    # VALIDATION
    # ------------------
    if not (MIN_RISK_PERCENT <= risk_percent <= MAX_RISK_PERCENT):
        return {
            "error": "Invalid risk_percent",
            "allowed_range": f"{MIN_RISK_PERCENT}% to {MAX_RISK_PERCENT}%"
        }

    if max_lot_size is not None:
        if not (MIN_LOT_SIZE <= max_lot_size <= MAX_LOT_SIZE):
            return {
                "error": "Invalid max_lot_size",
                "allowed_range": f"{MIN_LOT_SIZE} to {MAX_LOT_SIZE}"
            }

    # ------------------
    # MARKET DATA
    # ------------------
    df = data_router.fetch_ohlcv(symbol, interval)

    signal = strategy.generate_signal(df)
    trend = trend_engine.classify_trend(df)
    entry = float(df.close.iloc[-1])

    rsi_value = getattr(strategy, "last_rsi", 50.0)
    ema_slope = getattr(strategy, "ema_slope", 0.0)

    stop = take_profit = None
    sizing = None
    trade_allowed = False

    # ------------------
    # TRADE LOGIC
    # ------------------
    if signal in ("BUY", "SELL"):
        stop = fixed_percentage_stop(entry, 0.01, signal)
        take_profit = fixed_rr_take_profit(entry, stop, 2, signal)

        trade_allowed = validate_trade(
            signal=signal,
            trend=trend,
            entry=entry,
            stop_loss=stop,
            take_profit=take_profit
        )

        if trade_allowed:
            sizing = PositionSizer.calculate_position(
                symbol=symbol,
                balance=ACCOUNT_BALANCE,
                risk_percent=risk_percent,
                entry_price=entry,
                stop_loss=stop
            )

            # ------------------
            # HARD SAFETY FLOOR
            # ------------------
            if sizing["lots"] < MIN_LOT_SIZE:
                sizing["lots"] = MIN_LOT_SIZE
                sizing["units"] = MIN_LOT_SIZE * sizing["units_per_lot"]

            # ------------------
            # USER MAX LOT CAP
            # ------------------
            if max_lot_size is not None and sizing["lots"] > max_lot_size:
                sizing["lots"] = max_lot_size
                sizing["units"] = max_lot_size * sizing["units_per_lot"]

    # ------------------
    # ANALYTICS
    # ------------------
    volatility = calculate_volatility(df)

    confidence = calculate_confidence(
        structure_score=0.7,
        indicator_score=0.8,
        volume_score=0.6,
        volatility_score=0.7
    )

    # ------------------
    # RE-CHECK ENGINE
    # ------------------
    recheck_advice = None

    if not trade_allowed:
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

        schedule_recheck(symbol, recheck_advice)

    # ------------------
    # RESPONSE
    # ------------------
    response = {
        "symbol": symbol,
        "interval": interval,
        "signal": signal,
        "trend": trend,
        "entry_price": round(entry, 4),
        "stop_loss": round(stop, 4) if stop else None,
        "take_profit": round(take_profit, 4) if take_profit else None,
        "volatility": volatility,
        "confidence_percent": confidence,
        "trade_allowed": trade_allowed,
        "risk_percent": risk_percent,
        "lot_constraints": {
            "min_lot": MIN_LOT_SIZE,
            "max_lot": MAX_LOT_SIZE,
            "user_cap": max_lot_size
        }
    }

    if sizing:
        response.update({
            "position_size": round(sizing["units"], 2),
            "lot_size": round(sizing["lots"], 3),
            "risk_amount": round(sizing["risk_amount"], 2),
            "pip_distance": round(sizing["pip_distance"], 4)
        })

    if recheck_advice:
        response["recheck_advice"] = recheck_advice

    return response
