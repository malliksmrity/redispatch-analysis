"""
fetch_smard_generation.py
-------------------------
Pull "Actual electricity generation" by energy source for Germany (region "DE")
from the SMARD (Bundesnetzagentur) chart_data API, at HOURLY resolution, for the
most recent ~18 months, and save one tidy wide CSV.

Why this file exists
--------------------
SMARD has no bulk "give me everything" endpoint. Its public JSON API works in two
steps, exactly as documented by the community wrapper github.com/bundesAPI/smard-api:

  1. INDEX call  -> list of available "block" start-timestamps for a series
       https://www.smard.de/app/chart_data/{filter}/{region}/index_{resolution}.json
  2. DATA call   -> the actual points for ONE block
       https://www.smard.de/app/chart_data/{filter}/{region}/{filter}_{region}_{resolution}_{timestamp}.json

At hourly/quarter-hourly resolution each "block" is ONE WEEK, so 18 months is ~80
weekly files *per* energy source. We loop.

No third-party packages: uses only the Python standard library (urllib, json, csv).
pandas is used ONLY at the end for the quick sanity print; the CSV it writes is
plain text and can be re-read however you like.
"""

import csv
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- configuration ----------------------------------------------------------

REGION = "DE"                 # Germany (whole country / DE-LU market area label used by SMARD)
RESOLUTION = "hour"           # "hour" or "quarterhour" both exist for actual generation
MONTHS_BACK = 18              # how much recent history to keep
OUT_PATH = Path("data/raw/smard_generation_hourly.csv")

# SMARD numeric "filter" IDs for ACTUAL generation by source.
# Source: bundesAPI/smard-api README + bundesAPI/deutschland SMARD docs, cross-checked
# by fetching each index_hour.json (all return 200 with weekly blocks back to 2015).
GENERATION_FILTERS = {
    1223: "Lignite",              # Braunkohle
    1224: "Nuclear",              # Kernenergie
    1225: "Wind offshore",        # Wind Offshore
    1226: "Hydro",                # Wasserkraft (run-of-river)
    1227: "Other conventional",   # Sonstige Konventionelle
    1228: "Other renewable",      # Sonstige Erneuerbare
    4066: "Biomass",              # Biomasse
    4067: "Wind onshore",         # Wind Onshore
    4068: "Solar",                # Photovoltaik
    4069: "Hard coal",            # Steinkohle
    4070: "Pumped storage",       # Pumpspeicher (generation side)
    4071: "Natural gas",          # Erdgas
}

BASE = "https://www.smard.de/app/chart_data"
USER_AGENT = "Mozilla/5.0 (student data-viz coursework; contact via course)"

# --- tiny HTTP helper -----------------------------------------------------------

def get_json(url, retries=3, pause=1.5):
    """GET a URL and parse JSON, with a couple of retries for flaky network."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:                     # broad on purpose: network is the risk here
            if attempt == retries:
                raise
            print(f"    retry {attempt} for {url.split('/')[-1]} ({exc})")
            time.sleep(pause * attempt)


# --- main pull ----------------------------------------------------------------

def fetch_source(filter_id):
    """Return {timestamp_ms: value} for one energy source over the kept window."""
    index_url = f"{BASE}/{filter_id}/{REGION}/index_{RESOLUTION}.json"
    all_blocks = get_json(index_url)["timestamps"]     # list of week-start epochs in ms

    # Keep only weekly blocks that can contain data from the last MONTHS_BACK months.
    cutoff = datetime.now(timezone.utc) - timedelta(days=MONTHS_BACK * 30 + 7)
    cutoff_ms = int(cutoff.timestamp() * 1000)
    blocks = [b for b in all_blocks if b >= cutoff_ms]

    points = {}
    for block_ts in blocks:
        data_url = f"{BASE}/{filter_id}/{REGION}/{filter_id}_{REGION}_{RESOLUTION}_{block_ts}.json"
        series = get_json(data_url)["series"]          # list of [timestamp_ms, value_or_null]
        for ts, value in series:
            points[ts] = value
        time.sleep(0.15)                               # be polite to the server
    return points


def main():
    print(f"SMARD actual generation | region={REGION} | resolution={RESOLUTION} | "
          f"last {MONTHS_BACK} months")
    per_source = {}
    for fid, label in GENERATION_FILTERS.items():
        print(f"  {label:<20} (filter {fid}) ...", end=" ", flush=True)
        per_source[label] = fetch_source(fid)
        print(f"{len(per_source[label])} hourly points")

    # Union of all timestamps, sorted -> the rows of our table.
    all_ts = sorted(set().union(*[d.keys() for d in per_source.values()]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    header = ["timestamp_utc"] + list(GENERATION_FILTERS.values())
    with OUT_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for ts in all_ts:
            iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            row = [iso] + [per_source[label].get(ts, "") for label in GENERATION_FILTERS.values()]
            writer.writerow(row)

    print(f"\nwrote {OUT_PATH}  ({len(all_ts)} rows x {len(GENERATION_FILTERS)} sources)")

    # --- quick sanity check with pandas (not part of the data pipeline) --------
    import pandas as pd
    df = pd.read_csv(OUT_PATH, parse_dates=["timestamp_utc"])
    print("\nshape:", df.shape)
    print("date range:", df["timestamp_utc"].min(), "->", df["timestamp_utc"].max())
    print("\ndtypes:\n", df.dtypes)
    print("\nmissing values per column:\n", df.isna().sum())
    print("\nhead:\n", df.head())
    print("\ntail:\n", df.tail())


if __name__ == "__main__":
    main()
