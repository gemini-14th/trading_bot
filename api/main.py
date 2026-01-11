from fastapi import FastAPI, Query

from data.market_data_router import MarketDataRouter
from strategy.ema_rsi_strategy import EMARsiStrategy
from risk.stop_loss import fixed_percentage_stop
from risk.take_profit import fixed_rr_take_profit
from risk.position_sizer import PositionSizer
from analytics.trend_engine import TrendEngine
from analytics.volatility import calculate_volatility
from analytics.confidence_score import calculate_confidence
from data.validators import validate_trade

from execution.order_builder import OrderBuilder
from execution.brokers.paper import PaperBroker
from execution.brokers.mt5 import MT5Bridge

app = FastAPI(title="Trading Analysis Chatbot")

# ==============================
# CONFIG
# ==============================
ACCOUNT_BALANCE = 100_000

ALLOWED_RISK_LEVELS = {0.1, 0.5, 1.0, 2.0}
DEFAULT_RISK = 1.0

# ==============================
# ENGINES (Singletons)
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
    if risk_percent not in ALLOWED_RISK_LEVELS:
        return {
            "error": "Invalid risk_percent",
            "allowed_values": sorted(ALLOWED_RISK_LEVELS)
        }

    if max_lot_size is not None:
        if max_lot_size < 1 or max_lot_size > 100:
            return {
                "error": "Invalid max_lot_size",
                "allowed_range": "1 to 100"
            }

    # ------------------
    # MARKET DATA
    # ------------------
    df = data_router.fetch_ohlcv(symbol, interval)

    signal = strategy.generate_signal(df)
    trend = trend_engine.classify_trend(df)
    entry = float(df.close.iloc[-1])

    stop = take_profit = None
    sizing = None
    valid = False

    # ------------------
    # TRADE LOGIC
    # ------------------
    if signal in ("BUY", "SELL"):
        stop = fixed_percentage_stop(entry, 0.01, signal)
        take_profit = fixed_rr_take_profit(entry, stop, 2, signal)

        valid = validate_trade(
            signal=signal,
            trend=trend,
            entry=entry,
            stop_loss=stop,
            take_profit=take_profit
        )

        if valid:
            sizing = PositionSizer.calculate_position(
                symbol=symbol,
                balance=ACCOUNT_BALANCE,
                risk_percent=risk_percent,
                entry_price=entry,
                stop_loss=stop
            )

            # ------------------
            # LOT SIZE CAP
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
        "trade_allowed": valid,
        "risk_percent": risk_percent,
        "max_lot_size": max_lot_size
    }

    if sizing:
        response.update({
            "position_size": round(sizing["units"], 2),
            "lot_size": round(sizing["lots"], 3),
            "risk_amount": round(sizing["risk_amount"], 2),
            "pip_distance": round(sizing["pip_distance"], 4)
        })

    return response

# ==============================
# SCAN
# ==============================
@app.get("/scan")
def scan(
    symbols: str = Query(..., description="Comma-separated symbols"),
    interval: str = "1h"
):
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = []

    for symbol in symbol_list:
        try:
            df = data_router.fetch_ohlcv(symbol, interval)
            signal = strategy.generate_signal(df)
            trend = trend_engine.classify_trend(df)

            confidence = calculate_confidence(
                structure_score=0.7,
                indicator_score=0.8,
                volume_score=0.6,
                volatility_score=0.7
            )

            results.append({
                "symbol": symbol,
                "signal": signal,
                "trend": trend,
                "confidence": confidence
            })

        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e)
            })

    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return results

# ==============================
# EXECUTION
# ==============================
@app.post("/execute/paper")
def execute_paper_trade(analysis: dict):
    order = OrderBuilder.build_from_analysis(analysis)
    return paper_broker.execute(order)

@app.post("/execute/mt5")
def generate_mt5_order(analysis: dict):
    order = OrderBuilder.build_from_analysis(analysis)
    return MT5Bridge.generate(order)
