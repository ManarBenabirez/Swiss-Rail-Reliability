"""
Reproducible data download (Part 1).

Downloads from opentransportdata.swiss (licence: open use, source must be cited):
  1. Ist-Daten v2 ("actual data"): one CSV per day (~400-650 MB each) with the
     planned and actual arrival/departure time of every public transport stop.
  2. Service points v2: the official station list (ID, name, canton, coordinates).

The file links contain random IDs, so we do not hard-code them: we ask the
portal's catalogue API (CKAN) for the list of files and pick the dates we want.

Examples:
  python scripts/download_data.py --days 7                 # the 7 most recent days
  python scripts/download_data.py --start 2026-09-01 --end 2026-09-14
  python scripts/download_data.py --list                   # only show available days
"""
import argparse
import io
import os
import re
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
ISTDATEN_DIR = DATA_DIR / "raw" / "istdaten"
STATIONS_DIR = DATA_DIR / "raw" / "service_points"

# Two mirrors of the same catalogue; the second is used if the first fails.
CKAN_APIS = [
    "https://data.opentransportdata.swiss/api/3/action/package_show",
    "https://ckan.opendata.swiss/api/3/action/package_show",
]
ISTDATEN_DATASET = "ist-daten-v2"
STATIONS_DATASET = "service-point-v2"

HEADERS = {"User-Agent": "DISS-DPA student project (Swiss rail reliability)"}
DATE_IN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})_istdaten", re.IGNORECASE)


def list_resources(dataset_id):
    last_error = None
    for api in CKAN_APIS:
        try:
            r = requests.get(api, params={"id": dataset_id}, headers=HEADERS, timeout=60)
            r.raise_for_status()
            return r.json()["result"]["resources"]
        except Exception as e:  # try the next mirror
            last_error = e
            print(f"  ! catalogue {api} failed: {e}")
    sys.exit(f"Could not list dataset '{dataset_id}': {last_error}")


def download(url, target: Path, retries=3):
    """Stream a (big) file to disk. Skips files that are already complete."""
    if target.exists() and target.stat().st_size > 0:
        print(f"  = already downloaded: {target.name}")
        return target
    tmp = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                done = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            print(f"\r  ↓ {target.name}: {done/1e6:,.0f} / {total/1e6:,.0f} MB",
                                  end="", flush=True)
            print()
            tmp.rename(target)
            return target
        except Exception as e:
            print(f"\n  ! attempt {attempt}/{retries} failed for {target.name}: {e}")
            time.sleep(5 * attempt)
    sys.exit(f"Giving up on {url}")


def istdaten_days():
    """{date: url} for every daily file in the catalogue."""
    days = {}
    for res in list_resources(ISTDATEN_DATASET):
        text = f"{res.get('name', '')} {res.get('url', '')}"
        m = DATE_IN_NAME.search(text)
        if m and res.get("url"):
            days[date.fromisoformat(m.group(1))] = res["url"]
    return dict(sorted(days.items()))


def download_stations():
    STATIONS_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [r for r in list_resources(STATIONS_DATASET)
                  if "service-point" in f"{r.get('name','')} {r.get('url','')}".lower()
                  and r.get("url", "").lower().endswith((".csv", ".zip"))]
    if not candidates:
        sys.exit("No service point CSV found in the catalogue.")
    # Prefer the 'full' list, then the most recently modified file.
    candidates.sort(key=lambda r: ("full" in r["url"].lower(), r.get("last_modified") or ""),
                    reverse=True)
    url = candidates[0]["url"]
    print(f"Station list: {url}")
    if url.lower().endswith(".zip"):
        r = requests.get(url, headers=HEADERS, timeout=300)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for name in z.namelist():
                if name.lower().endswith(".csv"):
                    (STATIONS_DIR / "service_points.csv").write_bytes(z.read(name))
    else:
        download(url, STATIONS_DIR / "service_points.csv")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--days", type=int, default=7, help="number of most recent days (default 7)")
    p.add_argument("--start", type=date.fromisoformat, help="first day, YYYY-MM-DD")
    p.add_argument("--end", type=date.fromisoformat, help="last day, YYYY-MM-DD")
    p.add_argument("--list", action="store_true", help="only list the available days")
    p.add_argument("--skip-stations", action="store_true")
    args = p.parse_args()

    days = istdaten_days()
    if not days:
        sys.exit("No daily Ist-Daten files found in the catalogue.")
    print(f"Catalogue: {len(days)} daily files, from {min(days)} to {max(days)}")
    if args.list:
        for d in days:
            print(" ", d)
        return

    if args.start or args.end:
        start, end = args.start or min(days), args.end or max(days)
        chosen = [d for d in days if start <= d <= end]
    else:
        chosen = list(days)[-args.days:]
    if not chosen:
        sys.exit("No file in the requested date range (use --list to see what exists).")

    print(f"Downloading {len(chosen)} day(s): {chosen[0]} -> {chosen[-1]}")
    ISTDATEN_DIR.mkdir(parents=True, exist_ok=True)
    for d in chosen:
        download(days[d], ISTDATEN_DIR / f"{d.isoformat()}_IstDaten.csv")

    if not args.skip_stations:
        download_stations()

    total = sum(f.stat().st_size for f in DATA_DIR.joinpath("raw").rglob("*.csv"))
    print(f"\nDone. Raw data on disk: {total/1e9:.2f} GB in {DATA_DIR/'raw'}")


if __name__ == "__main__":
    main()
