from data.market_data_router import MarketDataRouter
from strategy.ema_rsi_strategy import EMARsiStrategy
from analytics.trend_engine import TrendEngine
from analytics.volatility import calculate_volatility
from analytics.confidence_score import calculate_confidence
from analytics.recheck_engine import RecheckDecisionEngine
from analytics.signal_validator import SignalValidator
from analytics.signal_ranker import SignalRanker
from analytics.signal_dispatcher import SignalDispatcher
from data.validators import validate_trade

from risk.stop_loss import fixed_percentage_stop
from risk.take_profit import fixed_rr_take_profit
from risk.position_sizer import PositionSizer

from notifications.recheck_scheduler import schedule_recheck


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
    CORE ANALYSIS SERVICE
    Manual error handling, consistent JSON response for errors
    """

    # ------------------
    # MARKET DATA
    # ------------------
    try:
        df = data_router.fetch_ohlcv(symbol, interval)
    except Exception as e:
        return {
            "error": f"Failed to fetch market data for {symbol} ({interval})",
            "suggestion": "Check symbol, interval, or data source connectivity"
        }

    try:
        signal = strategy.generate_signal(df)
    except Exception as e:
        return {
            "error": "Failed to generate trading signal",
            "suggestion": "Check strategy configuration"
        }

    try:
        trend = trend_engine.classify_trend(df)
    except Exception as e:
        return {
            "error": "Failed to classify market trend",
            "suggestion": "Check trend engine logic"
        }

    try:
        entry = float(df.close.iloc[-1])
    except Exception as e:
        return {
            "error": "Failed to determine entry price",
            "suggestion": "Check OHLCV data integrity"
        }

    rsi_value = getattr(strategy, "last_rsi", 50.0)
    ema_slope = getattr(strategy, "ema_slope", 0.0)

    stop = take_profit = None
    sizing = None
    trade_allowed = False
    lot_mode = "auto"
    rr_ratio = None

    # ------------------
    # TRADE LOGIC
    # ------------------
    if signal in ("BUY", "SELL"):
        try:
            stop = fixed_percentage_stop(entry, 0.01, signal)
        except Exception as e:
            return {
                "error": "Failed to calculate stop loss",
                "suggestion": "Check stop loss calculation logic"
            }

        try:
            take_profit = fixed_rr_take_profit(entry, stop, 2, signal)
        except Exception as e:
            return {
                "error": "Failed to calculate take profit",
                "suggestion": "Check take profit calculation logic"
            }

        try:
            trade_allowed = validate_trade(
                signal=signal,
                trend=trend,
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit
            )
        except Exception as e:
            return {
                "error": "Trade validation failed",
                "suggestion": "Check trade validation logic"
            }

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
                except Exception as e:
                    return {
                        "error": "Failed to calculate position from lot size",
                        "suggestion": "Check lot size or position sizing logic"
                    }
            else:
                try:
                    sizing = PositionSizer.calculate_position(
                        symbol=symbol,
                        balance=account_balance,
                        risk_percent=risk_percent,
                        entry_price=entry,
                        stop_loss=stop
                    )
                    if sizing["lots"] < min_lot:
                        return {
                            "error": "Account balance too small for safe trading",
                            "suggestion": "Reduce risk percent or use higher timeframe"
                        }
                except Exception as e:
                    return {
                        "error": "Failed to calculate position sizing",
                        "suggestion": "Check account balance, risk percent, or lot limits"
                    }

            if sizing:
                try:
                    rr_ratio = abs(take_profit - entry) / abs(entry - stop)
                except Exception as e:
                    rr_ratio = None  # optional fallback

    # ------------------
    # ANALYTICS
    # ------------------
    try:
        volatility = calculate_volatility(df)
    except Exception as e:
        return {
            "error": "Failed to calculate market volatility",
            "suggestion": "Check OHLCV data or volatility calculation"
        }

    try:
        confidence = calculate_confidence(
            structure_score=0.7,
            indicator_score=0.8,
            volume_score=0.6,
            volatility_score=0.7
        )
    except Exception as e:
        return {
            "error": "Failed to calculate confidence score",
            "suggestion": "Check confidence calculation logic"
        }

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

            schedule_recheck(symbol, recheck_advice)
        except Exception as e:
            return {
                "error": "Failed to generate recheck advice",
                "suggestion": "Check RecheckDecisionEngine or scheduler logic"
            }

    # ------------------
    # SIGNAL DISPATCH
    # ------------------
    if trade_allowed and sizing:
        try:
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
                "volatility": volatility
            }

            valid, _ = SignalValidator.validate(signal_payload)
            if valid:
                highlighted = SignalRanker.is_high_profit(signal_payload)
                SignalDispatcher.send(signal_payload, highlighted)
        except Exception as e:
            return {
                "error": "Failed to dispatch signal",
                "suggestion": "Check signal validation or dispatch logic"
            }

    # ------------------
    # RETURN RESULT
    # ------------------
    return {
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
        "lot_mode": lot_mode,
        "sizing": sizing,
        "recheck_advice": recheck_advice
    }
