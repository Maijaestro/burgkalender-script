from ics import Calendar, Event
from datetime import datetime, timedelta
import json, pytz, hashlib


def generate_uid(event):
    event_date = datetime.fromisoformat(event["event_date"]).date()
    unique_string = f"{event['event_artist']}_{event_date}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def run():
    # JSON-Datei laden
    with open("events.json", "r", encoding="utf-8") as f:
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
    with open("events.ics", "w") as f:
        f.writelines(calendar)


if __name__ == "__main__":
    run()
