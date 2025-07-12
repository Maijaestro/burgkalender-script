import json
import os
import re


def migrate_events202507(filename: str = "events.json") -> None:
    new_events = {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            old_events = json.load(f)

        for key, data in old_events.items():
            # Ort über event_location prüfen statt im Schlüssel
            if "Altes Rathaus" in data.get("event_location", ""):
                continue  # ⛔ Event wird ignoriert

            artist = data.get("event_artist", "Unbekannter Künstler")
            if re.search(r"vom\s+\d{1,2}\.\s*[-–]", artist):
                continue

            # Schlüssel zerlegen
            parts = key.split(" - ", 1)
            if len(parts) != 2:
                print(f"⚠️ Ungültiger Schlüssel: {key}")
                continue

            date_str = parts[0]

            migrated_key = f"{date_str} - {artist}"
            new_events[migrated_key] = data

        # Sortierte Speicherung
        sorted_events = dict(sorted(new_events.items()))

        with open(filename, "w", encoding="utf-8") as f_out:
            json.dump(sorted_events, f_out, indent=4, ensure_ascii=False)

        print(f"✅ Migration erfolgreich. Datei gespeichert: {filename}")

    except Exception as e:
        print(f"💥 Fehler bei der Migration: {e}")


if __name__ == "__main__":
    migrate_events202507()
