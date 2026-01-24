from datetime import datetime

HIGH_IMPACT_NEWS = [
    {"currency": "USD", "event": "CPI", "time_utc": "14:00"},
    {"currency": "USD", "event": "FOMC", "time_utc": "18:00"},
]

SYMBOL_CURRENCY_MAP = {
    "EUR/USD": ["EUR", "USD"],
    "GBP/USD": ["GBP", "USD"],
    "XAU/USD": ["USD"],
    "BTC/USD": ["USD"]
}

class NewsDecisionEngine:

    @staticmethod
    def check_news(symbol: str, now_utc: datetime):
        currencies = SYMBOL_CURRENCY_MAP.get(symbol, [])
        warnings = []

        for news in HIGH_IMPACT_NEWS:
            if news["currency"] not in currencies:
                continue

            event_time = datetime.strptime(news["time_utc"], "%H:%M").replace(
                year=now_utc.year,
                month=now_utc.month,
                day=now_utc.day
            )

            minutes = (event_time - now_utc).total_seconds() / 60

            if -15 <= minutes <= 60:
                warnings.append({
                    "event": news["event"],
                    "currency": news["currency"],
                    "minutes_to_event": int(minutes),
                    "recheck_after_minutes": 30
                })

        return warnings