from fastapi import FastAPI, Query, HTTPException

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
from services.analyse_service import analyze_market

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
    # account_balance: float = 0.0 ,
    risk_percent: float = DEFAULT_RISK,
    lot_size: float | None = None
):
    # ------------------
    # VALIDATION (API ONLY)
    # ------------------
    if not (MIN_RISK_PERCENT <= risk_percent <= MAX_RISK_PERCENT):
        raise HTTPException(status_code=400, detail={
            "error": "Invalid risk_percent",
            "allowed_range": f"{MIN_RISK_PERCENT}% to {MAX_RISK_PERCENT}%"
        })

    if lot_size is not None and not (MIN_LOT_SIZE <= lot_size <= MAX_LOT_SIZE):
        raise HTTPException(status_code=400, detail={
            "error": "Invalid lot_size",
            "allowed_range": f"{MIN_LOT_SIZE} to {MAX_LOT_SIZE}"
        })
    
    if account_balance <= 0:
        raise HTTPException(status_code=400, detail={
            "error": "account_balance must be greater than 0"
        })

    result = analyze_market(
        symbol=symbol,
        interval=interval,
        account_balance=account_balance,
        risk_percent=risk_percent,
        lot_size=lot_size,
        min_lot=MIN_LOT_SIZE,
        max_lot=MAX_LOT_SIZE
    )


    # ------------------
    # SERVICE ERROR HANDLING
    # ------------------
    if "error" in result:
        # Map all service errors to HTTP 400 for now
        raise HTTPException(status_code=400, detail=result)


    # ------------------
    # RESPONSE FORMAT
    # ------------------
    if "sizing" in result and result["sizing"]:
        result.update({
            "recommended_lot_size": round(result["sizing"]["lots"], 4),
            "position_size": round(result["sizing"]["units"], 2),
            "risk_amount": round(result["sizing"]["risk_amount"], 2),
            "actual_risk_percent": round(result["sizing"]["actual_risk_percent"], 2),
            "pip_distance": round(result["sizing"]["pip_distance"], 2)
        })
        result.pop("sizing")

    return result