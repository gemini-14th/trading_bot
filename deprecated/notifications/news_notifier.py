import os

WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"

def send_whatsapp_alert(message: str):
    if not WHATSAPP_ENABLED:
        return

    try:
        from twilio.rest import Client

        client = Client(
            os.getenv("TWILIO_SID"),
            os.getenv("TWILIO_TOKEN")
        )

        client.messages.create(
            from_="whatsapp:" + os.getenv("TWILIO_FROM"),
            to="whatsapp:" + os.getenv("TWILIO_TO"),
            body=message
        )

    except Exception as e:
        print("WhatsApp alert failed:", e)