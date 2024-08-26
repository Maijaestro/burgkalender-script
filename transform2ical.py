from ics import Calendar, Event
from datetime import datetime, timedelta
import json, pytz


def run():
    # JSON-Datei laden
    with open("events.json", "r", encoding="utf-8") as f:
        events_data = json.load(f)

    # Kalender erstellen
    calendar = Calendar()

    # Zeitzone setzen
    tz = pytz.timezone("Europe/Berlin")

    # Ereignisse hinzufügen
    for date, event in events_data.items():
        e = Event()
        e.name = event["event_artist"]

        start_time = datetime.strptime(event["event_starttime"], "%Y-%m-%d %H:%M")
        start_time = tz.localize(start_time)
        e.begin = start_time
        e.duration = timedelta(hours=2)

        e.location = event["event_location"]

        e.url = event["event_info"]

        calendar.events.add(e)

    # iCal-Datei speichern
    with open("events.ics", "w") as f:
        f.writelines(calendar)


if __name__ == "__main__":
    run()
