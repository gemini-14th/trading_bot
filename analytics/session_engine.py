from datetime import datetime, timezone


class MarketSessionEngine:

    SESSIONS = {
        "ASIA": (0, 9),
        "LONDON": (7, 16),
        "NEW_YORK": (13, 22),
    }


    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)


    @staticmethod
    def is_weekend() -> bool:

        now = MarketSessionEngine.utc_now()
        wd = now.weekday()
        hr = now.hour

        # Saturday
        if wd == 5:
            return True

        # Sunday before open
        if wd == 6 and hr < 22:
            return True

        # Friday after close
        if wd == 4 and hr >= 22:
            return True

        return False


    @staticmethod
    def get_active_sessions():

        hour = MarketSessionEngine.utc_now().hour

        active = []

        for name, (start, end) in MarketSessionEngine.SESSIONS.items():
            if start <= hour < end:
                active.append(name)

        return active


    @staticmethod
    def is_killzone() -> bool:
        """
        London-NY overlap
        """
        hour = MarketSessionEngine.utc_now().hour

        return 13 <= hour <= 16


    @staticmethod
    def market_status():

        now = MarketSessionEngine.utc_now()

        return {
            "utc_time": now.isoformat(),
            "weekday": now.strftime("%A"),
            "hour": now.hour,
            "weekend": MarketSessionEngine.is_weekend(),
            "active_sessions": MarketSessionEngine.get_active_sessions(),
            "killzone": MarketSessionEngine.is_killzone()
        }
