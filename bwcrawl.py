import requests, json, dateparser, os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from bs4 import BeautifulSoup


def run():
    url = "https://www.burg-wilhelmstein.com/tickets/"

    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        # Set a timeout of 10 seconds
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            events = {}

            for event in soup.find_all("article"):
                # Artist
                artist_text = event.find(class_="mec-event-title").get_text(strip=True)

                # Date
                date_raw = event.find(class_="mec-event-date").get_text(strip=True)
                time_raw = (
                    event.find(class_="mec-start-time").get_text(strip=True)
                    if event.find(class_="mec-start-time")
                    else "00:00"
                )

                date = dateparser.parse(date_raw)

                datetime_string = f"{date.strftime('%Y-%m-%d')} {time_raw}"
                event_date = datetime.strptime(
                    datetime_string, "%Y-%m-%d %H:%M"
                ).isoformat()

                # Location
                location_text = event.find(class_="mec-events-address").get_text(
                    strip=True
                )

                # Info
                info_text = event.find(class_="mec-booking-button").get("href")

                # Key
                key_text = date.strftime("%Y-%m-%d") + " - " + location_text

                events.update(
                    {
                        key_text: {
                            "event_artist": artist_text,
                            "event_date": event_date,
                            "event_location": location_text,
                            "event_info": info_text,
                        }
                    }
                )

            filename = "events.json"
            filename_backup = "events.json.bak"
            filename_temp = "events.json.tmp"

            try:
                with open(filename, "r", encoding="utf-8") as f:
                    old_events = json.load(f)
                old_events.update(events)
            except FileNotFoundError:
                old_events = events

            try:
                if os.path.exists(filename):
                    os.rename(filename, filename_backup)

                with open(filename_temp, "w", encoding="utf-8") as json_file:
                    json.dump(old_events, json_file, indent=4, ensure_ascii=False)

                os.rename(filename_temp, filename)

                if os.path.exists(filename_backup):
                    os.remove(filename_backup)
            except Exception as e:
                if os.path.exists(filename_temp):
                    os.remove(filename_temp)
                if os.path.exists(filename_backup):
                    os.rename(filename_backup, filename)

            pass
        else:
            print(f"Fehler beim Abrufen der Seite: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Die Anfrage hat zu lange gedauert und wurde abgebrochen.")
    except requests.exceptions.RequestException as e:
        print(f"Ein Fehler ist aufgetreten: {e}")


if __name__ == "__main__":
    run()
