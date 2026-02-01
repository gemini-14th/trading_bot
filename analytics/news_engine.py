
import requests
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET


class NewsEngine:

    FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"


    @staticmethod
    def fetch_events():

        try:
            r = requests.get(NewsEngine.FEED_URL, timeout=10)
            r.raise_for_status()

            root = ET.fromstring(r.text)
            return root.findall("event")

        except Exception:
            return []


    @staticmethod
    def get_high_impact_events():

        events = NewsEngine.fetch_events()
        high = []

        for e in events:

            impact = e.find("impact").text

            if impact != "High":
                continue

            date = e.find("date").text
            time = e.find("time").text

            try:
                dt = datetime.strptime(
                    f"{date} {time}",
                    "%m-%d-%Y %H:%M"
                ).replace(tzinfo=timezone.utc)

                high.append(dt)

            except Exception:
                continue

        return high


    @staticmethod
    def is_news_time(buffer_minutes=30) -> bool:

        now = datetime.now(timezone.utc)
        events = NewsEngine.get_high_impact_events()

        for event_time in events:

            delta = abs((event_time - now).total_seconds()) / 60

            if delta <= buffer_minutes:
                return True

        return False
