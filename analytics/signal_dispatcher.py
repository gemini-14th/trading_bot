import os
from notifications.whatsapp_notifier import send_whatsapp_message
from notifications.whatsapp_notifier import WhatsAppNotifier

notifier = WhatsAppNotifier()

class SignalDispatcher:

    @staticmethod
    def send(signal: dict, highlighted: bool = False):
        prefix = "⭐ HIGH-PROFIT SIGNAL ⭐\n" if highlighted else "📊 TRADE SIGNAL\n"

        message = f"""{prefix}
Symbol: {signal.get('symbol')}
Direction: {signal.get('signal')}
Timeframe: {signal.get('interval')}

Entry: {signal.get('entry_price')}
Stop Loss: {signal.get('stop_loss')}
Take Profit: {signal.get('take_profit')}

RR: {signal.get('rr_ratio')}
Confidence: {signal.get('confidence_percent')}%
Lot Size: {signal.get('lot_size')}
"""

        notifier.send_whatsapp_message(
            to_number=os.getenv("WHATSAPP_TO =+254705798519"),
            message=message
        )
