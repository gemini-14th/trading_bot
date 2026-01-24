from notifications.signal_cli_sender import SignalCLISender
from notifications.emailjs_sender import EmailJSSender

class SignalDispatcher:

    MODE = "signal"  # "signal" or "email"

    @classmethod
    def dispatch(cls, signal: dict):
        if cls.MODE == "signal":
            SignalCLISender.send(signal)
        elif cls.MODE == "email":
            EmailJSSender.send(signal)
