import requests
import os

class EmailJSSender:

    SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
    TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID")
    PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")

    @staticmethod
    def send(signal: dict):
        payload = {
            "service_id": EmailJSSender.SERVICE_ID,
            "template_id": EmailJSSender.TEMPLATE_ID,
            "user_id": EmailJSSender.PUBLIC_KEY,
            "template_params": {
                "symbol": signal["symbol"],
                "direction": signal["signal"],
                "entry": signal["entry_price"],
                "sl": signal["stop_loss"],
                "tp": signal["take_profit"],
                "confidence": signal["confidence_percent"],
                "expiry": signal["signal_validity"]["expires_at"]
            }
        }

        requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload
        )
