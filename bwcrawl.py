import re
import shutil
from typing import List, Tuple
import requests, json, os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dateparser import parse
from bs4 import BeautifulSoup


def runBurg(events) -> None:
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
            events_initial = soup.find_all("article")
            last_initial_date_tag = events_initial[-1].find(class_="mec-event-date")
            start_date = (
                last_initial_date_tag.get_text(strip=True)
                if last_initial_date_tag
                else "2025-07-01"
            )
            events_xhr = load_masonry_events(session, start_date=start_date)
            events_raw = events_initial + events_xhr

            for event in events_raw:
                # Künstler
                artist_tag = event.find(class_="mec-event-title")
                artist_text = (
                    artist_tag.get_text(strip=True)
                    if artist_tag
                    else "Unbekannter Künstler"
                )
                if re.search(r"vom\s+\d{1,2}\.\s*[-–]", artist_text):
                    print(f"⛔ Event übersprungen (Mehrtagesreihe): {artist_text}")
                    continue

                # Datum & Uhrzeit
                date_tag = event.find(class_="mec-event-date")
                time_tag = event.find(class_="mec-start-time")
                date_raw = date_tag.get_text(strip=True) if date_tag else ""
                time_raw = time_tag.get_text(strip=True) if time_tag else "00:00"
                datetime_string = f"{date_raw} {time_raw}"
                dt = parse(datetime_string)
                event_date = dt.isoformat()

                # Ort
                location_tag = event.find(class_="mec-events-address")
                location_text = (
                    location_tag.get_text(strip=True)
                    if location_tag
                    else "Unbekannter Ort"
                )
                if "Altes Rathaus" in location_text:
                    continue

                # Info-Link
                info_tag = event.find(class_="mec-booking-button")
                info_text = (
                    info_tag.get("href")
                    if info_tag and info_tag.has_attr("href")
                    else None
                )

                key_text = f"{dt.strftime("%Y-%m-%d")} - {artist_text}"

                events[key_text] = {
                    "event_artist": artist_text,
                    "event_date": event_date,
                    "event_location": location_text,
                    "event_info": info_text,
                }
            pass
        else:
            print(f"Fehler beim Abrufen der Seite: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Die Anfrage hat zu lange gedauert und wurde abgebrochen.")
    except requests.exceptions.RequestException as e:
        print(f"Ein Fehler ist aufgetreten: {e}")


def runDasDa(events) -> None:
    url = "https://dasda.de/"

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

            for event in soup.find_all(class_="c-play__grid"):
                tag_spans = event.select("span.c-play__tags span.c-tag")
                if not any(tag.get_text(strip=True) == "Open Air" for tag in tag_spans):
                    continue

                # Info
                info_text = event.select_one("a.c-play__image-container")["href"]

                title_text, dates = processLink(info_text, session)

                # Artist
                artist_text = "DAS DA Theater - " + title_text

                # Location
                location_text = "Burg Wilhelmstein, 52146 Würselen"

                for date_raw in dates:
                    # Date
                    date = parse(date_raw)
                    event_date = date.isoformat()

                    # Key
                    key_text = f"{date.strftime("%Y-%m-%d")} - {artist_text}"

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
            pass
        else:
            print(f"Fehler beim Abrufen der Seite: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Die Anfrage hat zu lange gedauert und wurde abgebrochen.")
    except requests.exceptions.RequestException as e:
        print(f"Ein Fehler ist aufgetreten: {e}")


def saveToFile(events: dict, filename: str = "events.json") -> None:
    backup_file = filename + ".bak"
    temp_file = filename + ".tmp"

    try:
        with open(filename, "r", encoding="utf-8") as f:
            old_events = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        old_events = {}

    old_events.update(events)
    sorted_events = dict(sorted(old_events.items()))

    try:
        if os.path.exists(filename):
            shutil.copyfile(filename, backup_file)

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sorted_events, f, indent=4, ensure_ascii=False)

        os.replace(temp_file, filename)

        if os.path.exists(backup_file):
            os.remove(backup_file)

    except Exception as e:
        print(f"💥 Fehler beim Speichern: {e}")
        if os.path.exists(backup_file):
            shutil.copyfile(backup_file, filename)
        if os.path.exists(temp_file):
            os.remove(temp_file)


def processLink(url: str, session: requests.Session) -> Tuple[str, List[str]]:
    try:
        detail_response = session.get(url, timeout=10)
        if detail_response.status_code == 200:
            detail_soup = BeautifulSoup(detail_response.content, "html.parser")

            title = extract_event_title(detail_soup)
            dates = extract_event_dates(detail_soup)
            return title, dates
        return "Kein Titel", []
    except Exception as e:
        print(f"❗ Fehler beim Abrufen der Detailseite: {e}")


def extract_event_dates(detail_soup: BeautifulSoup) -> List[str]:
    dates = []
    events_container = detail_soup.select_one("div.c-play__events")
    if not events_container:
        return dates

    date_links = events_container.select("a.c-event__button")

    for link in date_links:
        text = link.get_text(strip=True)
        if text:
            dates.append(text)

    return dates


def extract_event_title(detail_soup) -> str:
    title_tag = detail_soup.select_one("h1.c-teaser__title")
    if title_tag:
        return title_tag.get_text(separator=" ", strip=True)
    return "Kein Titel gefunden"


def load_masonry_events(session: requests.Session, start_date: str) -> list:
    url = "https://www.burg-wilhelmstein.com/wp-admin/admin-ajax.php"
    events_html = []
    offset = 1

    while True:
        payload = {
            "action": "mec_masonry_load_more",
            "mec_offset": str(offset),
            "mec_start_date": start_date,
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = session.post(url, data=payload, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        masonry_items = soup.find_all("article")

        if not masonry_items:
            break

        events_html.extend(masonry_items)

        last_date_tag = masonry_items[-1].find(class_="mec-event-date")
        new_start_date = (
            last_date_tag.get_text(strip=True) if last_date_tag else start_date
        )

        if new_start_date == start_date:
            break

        start_date = new_start_date
        offset += 1

    return events_html


if __name__ == "__main__":
    events = {}
    runBurg(events)
    runDasDa(events)
    saveToFile(events)
