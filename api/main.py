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
from analytics.signal_validator import SignalValidator
from analytics.signal_ranker import SignalRanker
from analytics.signal_dispatcher import SignalDispatcher
from api.user import router as users_router
from analytics.auto_signal_scanner import AutoSignalScanner
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Trading Analysis Chatbot")


# ==============================
# MIDDLEWARE
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)

# ==============================
# CONFIG
# ==============================
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

@app.post("/scan-and-send")
def scan_and_send(
    interval: str = "1h",
    account_balance: float = Query(..., gt=0),
    risk_percent: float = DEFAULT_RISK
):
    AutoSignalScanner.scan_and_dispatch(
        interval=interval,
        account_balance=account_balance,
        risk_percent=risk_percent
    )
    return {"status": "Signal scan completed"}

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
    account_balance: float = Query(..., gt=0),
    risk_percent: float = DEFAULT_RISK,
    lot_size: float | None = None
):
    # ------------------
    # VALIDATION
    # ------------------
    if not (MIN_RISK_PERCENT <= risk_percent <= MAX_RISK_PERCENT):
        return {
            "error": "Invalid risk_percent",
            "allowed_range": f"{MIN_RISK_PERCENT}% to {MAX_RISK_PERCENT}%"
        }

    if lot_size is not None and not (MIN_LOT_SIZE <= lot_size <= MAX_LOT_SIZE):
        return {
            "error": "Invalid lot_size",
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
    lot_mode = "auto"

    # ------------------
    # TRADE LOGIC WITH ENHANCED RISK
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
            if lot_size is not None:
                # MANUAL LOT MODE
                sizing = PositionSizer.calculate_from_lot(
                    symbol=symbol,
                    balance=account_balance,
                    lot_size=lot_size,
                    entry_price=entry,
                    stop_loss=stop
                )
                lot_mode = "manual"

            else:
                # AUTO SAFE MODE
                sizing = PositionSizer.calculate_position(
                    symbol=symbol,
                    balance=account_balance,
                    risk_percent=risk_percent,
                    entry_price=entry,
                    stop_loss=stop
                )
                lot_mode = "auto"

                if sizing["lots"] < MIN_LOT_SIZE:
                    return {
                        "error": "Account balance too small for safe trading",
                        "suggestion": "Reduce risk or use higher timeframe"
                    }

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

    if trade_allowed and sizing:
        rr_ratio = abs(take_profit - entry) / abs(entry - stop)

    signal_payload = {
        "symbol": symbol,
        "signal": signal,
        "interval": interval,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit": take_profit,
        "confidence_percent": confidence,
        "lot_size": sizing["lots"],
        "rr_ratio": round(rr_ratio, 2),
        "volatility": volatility
    }

    valid, reason = SignalValidator.validate(signal_payload)

    if valid:
        highlighted = SignalRanker.is_high_profit(signal_payload)
        SignalDispatcher.send(signal_payload, highlighted)

    # ------------------
    # RESPONSE
    # ------------------
    response = {
        "symbol": symbol,
        "interval": interval,
        "account_balance": account_balance,
        "signal": signal,
        "trend": trend,
        "entry_price": round(entry, 4),
        "stop_loss": round(stop, 4) if stop else None,
        "take_profit": round(take_profit, 4) if take_profit else None,
        "volatility": volatility,
        "confidence_percent": confidence,
        "trade_allowed": trade_allowed,
        "risk_percent": risk_percent,
        "lot_mode": lot_mode,
        "lot_constraints": {
            "min_lot": MIN_LOT_SIZE,
            "max_lot": MAX_LOT_SIZE
        }
    }

    if sizing:
        response.update({
            "recommended_lot_size": round(sizing["lots"], 4),
            "position_size": round(sizing["units"], 2),
            "risk_amount": round(sizing["risk_amount"], 2),
            "actual_risk_percent": round(sizing["actual_risk_percent"], 2),
            "pip_distance": round(sizing["pip_distance"], 2)
        })
        if lot_mode == "manual" and sizing["actual_risk_percent"] > risk_percent * 2:
            response["warning"] = "Manual lot size exceeds safe risk threshold"

    if recheck_advice:
        response["recheck_advice"] = recheck_advice

    return response

