import os
from datetime import datetime, timedelta
from notifications.whatsapp_notifier import WhatsAppNotifier


def schedule_recheck(symbol: str, recheck_advice: dict):
    """
    Placeholder scheduler.
    For now, it only sends a WhatsApp message immediately.
    """
    notifier = WhatsAppNotifier()

    if not recheck_advice:
        return

    message = (
        f"📊 Market Update Alert\n\n"
        f"Symbol: {symbol}\n"
        f"Reason: {recheck_advice.get('reason')}\n"
        f"Re-check in: {recheck_advice.get('recheck_in')}\n"
    )

    # ⚠️ Replace with user's WhatsApp later (Phase 3.2)
    demo_number = os.getenv("ADMIN_WHATSAPP_NUMBER")
    if demo_number:
        notifier.send_whatsapp_message(demo_number, message)
