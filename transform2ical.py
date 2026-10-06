from icalendar import Calendar, Event
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import json, pytz, hashlib, logging, re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# File path constants
EVENTS_JSON_FILE = "events.json"
EVENTS_ICAL_FILE = "events.ics"

# Matches a run of letters (incl. German umlauts/ß) plus embedded
# apostrophes, so e.g. "FIDDLER’S" is treated as one word. Hyphens are
# deliberately excluded so each side of a compound like "MO-TORRES" is
# capitalized independently ("Mo-Torres", not "Mo-torres").
_WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ'’‘]+")


def fix_screaming_caps(text: str) -> str:
    """Title-case words that are ALL CAPS in the source; leave already
    mixed-case / stylized words (e.g. "LaFee", "NightWash") untouched."""
    return _WORD_RE.sub(
        lambda m: m.group(0).capitalize() if m.group(0).isupper() else m.group(0),
        text,
    )


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
    calendar.add("prodid", "-//burgkalender//burgkalender-script//DE")
    calendar.add("version", "2.0")

    # Zeitzone setzen
    tz = pytz.timezone("Europe/Berlin")

    # Ereignisse hinzufügen (events.json can hold the same show under an old
    # time-less and a newer timed key; the UID is the same, so keep the first)
    seen_uids = set()
    for key, event in sorted(
        events_data.items(),
        key=lambda item: datetime.fromisoformat(item[1]["event_date"]),
    ):
        uid = generate_uid(event)
        if uid in seen_uids:
            continue
        seen_uids.add(uid)

        e = Event()
        e.add("summary", fix_screaming_caps(event["event_artist"]))

        start_time = datetime.fromisoformat(event["event_date"])
        if start_time.tzinfo is None:
            start_time = tz.localize(start_time)
        else:
            start_time = start_time.astimezone(tz)
        e.add("dtstart", start_time.astimezone(timezone.utc))
        e.add("duration", timedelta(hours=2))

        e.add("location", event["event_location"])

        e.add("url", event["event_info"])

        e.add("uid", uid)

        calendar.add_component(e)

    # iCal-Datei speichern
    with open(EVENTS_ICAL_FILE, "wb") as f:
        f.write(calendar.to_ical())

    logger.info(f"✓ Generated {EVENTS_ICAL_FILE} with {len(calendar.subcomponents)} events")


if __name__ == "__main__":
    run()
