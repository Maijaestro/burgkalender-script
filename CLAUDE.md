# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Automated event calendar scraper that crawls two event agencies' websites daily and publishes an `.ics` calendar file for a single venue: **Burg Wilhelmstein** in Würselen, Germany.

Both agencies also run events at other locations — the scrapers filter to only keep events actually held at the Burg:
- **Burg Wilhelmstein** (https://www.burg-wilhelmstein.com/tickets/) — their own concerts and theater events; excludes anything at "Altes Rathaus"
- **DAS DA Theater** (https://dasda.de/) — children's theater; excludes indoor/off-site shows, keeps only "Open Air" events at the Burg

Output: `events.json` (persistent store) and `events.ics` (iCalendar for subscription).

The script repo is private; CI pushes `events.ics` to a separate public repo (`Maijaestro/burgkalender`) for web publishing.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
# Full pipeline: crawl + generate ICS
python main.py

# Individual steps
python -c "import bwcrawl; bwcrawl.run()"
python -c "import transform2ical; transform2ical.run()"
```

The `updateEvents.sh` script handles cloning, venv creation, and execution in one step (used for local cron setup).

## Architecture

**main.py** → calls `bwcrawl.run()` then `transform2ical.run()`

**bwcrawl.py** — two scrapers + shared persistence:
- `runBurg()`: scrapes Burg Wilhelmstein ticket page; handles AJAX/masonry pagination via `load_masonry_events()`; filters out "Altes Rathaus" events and multi-day series
- `runDasDa()`: scrapes DAS DA Theater; follows detail page links to extract dates; filters to "Open Air" events only
- `saveToFile()`: merges new events into `events.json` (existing keys preserved, new data wins on conflict); uses atomic write via temp file + rename, keeps `.bak` backup

**transform2ical.py** — reads `events.json`, writes `events.ics`; assigns a default 2-hour duration (source sites don't reliably provide end times), Europe/Berlin timezone, MD5-based UIDs

**events.json** key format: `"YYYY-MM-DD - <location_short> - <artist>"`

## CI/CD

GitHub Actions (`.github/workflows/actions.yml`) runs daily at 06:00 UTC:
1. Runs `main.py`
2. Commits generated `events.json` and `events.ics` back to this repo
3. Copies `events.ics` to the separate public repo `Maijaestro/burgkalender`

Automated commits appear as "updated files" — normal behavior, not manual changes.

`events.json` and `events.ics` are intentionally committed: the second repo picks them up directly from this repo's main branch.
