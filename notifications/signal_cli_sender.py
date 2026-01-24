import subprocess

class SignalCLISender:

    PHONE_NUMBER = "+254705798519,+254 110 861797"  # your Signal number

    @staticmethod
    def send(signal: dict):
        message = f"""
📊 TRADE SIGNAL

Symbol: {signal['symbol']}
Direction: {signal['signal']}
Entry: {signal['entry_price']}
SL: {signal['stop_loss']}
TP: {signal['take_profit']}
Confidence: {signal['confidence_percent']}%
Valid Until: {signal['signal_validity']['expires_at']}
"""

        subprocess.run([
            "signal-cli",
            "send",
            SignalCLISender.PHONE_NUMBER,
            "-m",
            message
        ])
