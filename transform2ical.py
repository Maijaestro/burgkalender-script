from ics import Calendar, Event
from datetime import datetime, timedelta
from typing import Dict, Any
import json, pytz, hashlib, logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# File path constants
EVENTS_JSON_FILE = "events.json"
EVENTS_ICAL_FILE = "events.ics"


def generate_uid(event: Dict[str, Any]) -> str:
    event_date = datetime.fromisoformat(event["event_date"]).date()
    unique_string = f"{event['event_artist']}_{event_date}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def run() -> None:
    # JSON-Datei laden
    with open(EVENTS_JSON_FILE, "r", encoding="utf-8") as f:
        events_data = json.load(f)

    # Kalender erstellen
    calendar = Calendar()

    # Zeitzone setzen
    tz = pytz.timezone("Europe/Berlin")

    # Ereignisse hinzufügen
    for key, event in sorted(
        events_data.items(),
        key=lambda item: datetime.fromisoformat(item[1]["event_date"]),
    ):
        e = Event()
        e.name = event["event_artist"]

        start_time = datetime.fromisoformat(event["event_date"])
        start_time = tz.localize(start_time)
        e.begin = start_time
        e.duration = timedelta(hours=2)

        e.location = event["event_location"]

        e.url = event["event_info"]

        e.uid = generate_uid(event)

        calendar.events.add(e)

    # iCal-Datei speichern
    with open(EVENTS_ICAL_FILE, "w") as f:
        f.writelines(calendar)

    logger.info(f"✓ Generated {EVENTS_ICAL_FILE} with {len(calendar.events)} events")


if __name__ == "__main__":
    run()
