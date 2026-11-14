"""Field Shift -- TB.2: detect emergence/peak/harvest per season, per field.

Reads the smoothed daily data/ndvi_<field_id>.csv (ndvi_smooth column,
produced by TB.1 / engine/smooth_ndvi.py) and, for each soybean season
(planted ~Sep-Oct of year Y, harvested ~Jan-Feb of Y+1), finds:

  - the dry-season minimum (trough) in [Jun 1, Nov 30] of year Y
  - emergence: first date after the trough where ndvi_smooth crosses
    EMERGENCE_THRESHOLD rising
  - peak: the curve's maximum after emergence (only accepted once the
    data shows a confirmed decline afterwards -- otherwise the season is
    still in progress and peak/harvest are left blank)
  - harvest: first date after a confirmed peak where ndvi_smooth crosses
    EMERGENCE_THRESHOLD falling

Output: data/phenology_<field_id>.csv -- season, emergence_date,
peak_date, harvest_date (docs/CONTRACTS.md).

Run:
    python engine/detect_phenology.py
"""

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
FIELDS_PATH = REPO_ROOT / "data" / "fields.geojson"
DATA_DIR = REPO_ROOT / "data"

EMERGENCE_THRESHOLD = 0.35
PEAK_SEARCH_DAYS = 90  # how far past emergence to look for this season's peak
# (soybean emergence->peak is observed at <=60 days in our fields; 90 gives
# headroom without reaching into a safrinha second crop's own rise)
PEAK_CONFIRM_BUFFER_DAYS = 20  # data needed past the candidate peak to trust it
HARVEST_SEARCH_DAYS = 90  # how far past peak to look for the down-crossing


def load_smooth_series(field_id: str) -> pd.Series:
    df = pd.read_csv(DATA_DIR / f"ndvi_{field_id}.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")["ndvi_smooth"]


def find_up_crossing(series: pd.Series, after: pd.Timestamp, before: pd.Timestamp):
    window = series[(series.index > after) & (series.index <= before)]
    if len(window) < 2:
        return None
    prev_vals = window.shift(1)
    crossed = (prev_vals < EMERGENCE_THRESHOLD) & (window >= EMERGENCE_THRESHOLD)
    hits = window.index[crossed]
    return hits[0] if len(hits) else None


def find_down_crossing(series: pd.Series, after: pd.Timestamp, before: pd.Timestamp):
    window = series[(series.index > after) & (series.index <= before)]
    if len(window) < 2:
        return None
    prev_vals = window.shift(1)
    crossed = (prev_vals >= EMERGENCE_THRESHOLD) & (window < EMERGENCE_THRESHOLD)
    hits = window.index[crossed]
    return hits[0] if len(hits) else None


def detect_seasons(series: pd.Series) -> list[dict]:
    last_date = series.index.max()
    first_year = series.index.min().year
    last_year = last_date.year

    rows = []
    for year in range(first_year, last_year + 1):
        trough_start = pd.Timestamp(year=year, month=6, day=1)
        trough_end = min(pd.Timestamp(year=year, month=11, day=30), last_date)
        trough_window = series[(series.index >= trough_start) & (series.index <= trough_end)]
        if len(trough_window) < 30:
            continue  # not enough of the dry season observed yet
        trough_date = trough_window.idxmin()

        emergence_search_end = pd.Timestamp(year=year + 1, month=1, day=31)
        emergence_date = find_up_crossing(series, trough_date, emergence_search_end)
        if emergence_date is None:
            continue  # crop hasn't emerged yet (or never will -- no data that far)

        peak_search_end = min(
            emergence_date + pd.Timedelta(days=PEAK_SEARCH_DAYS), last_date
        )
        rising_window = series[(series.index >= emergence_date) & (series.index <= peak_search_end)]
        if rising_window.empty:
            continue
        peak_date = rising_window.idxmax()
        peak_value = rising_window.loc[peak_date]

        confirm_end = peak_date + pd.Timedelta(days=PEAK_CONFIRM_BUFFER_DAYS)
        buffer_window = series[(series.index > peak_date) & (series.index <= confirm_end)]
        not_enough_data = confirm_end > last_date
        exceeded_by_later_point = (buffer_window > peak_value).any()
        if not_enough_data or exceeded_by_later_point:
            # either too close to "today" to trust it, or the true peak is
            # still ahead (the window cut off before the curve turned down)
            rows.append(
                {
                    "season": f"{year}/{str(year + 1)[-2:]}",
                    "emergence_date": emergence_date.strftime("%Y-%m-%d"),
                    "peak_date": None,
                    "harvest_date": None,
                }
            )
            continue

        harvest_search_end = min(
            peak_date + pd.Timedelta(days=HARVEST_SEARCH_DAYS), last_date
        )
        harvest_date = find_down_crossing(series, peak_date, harvest_search_end)
        if harvest_date is None and harvest_search_end == peak_date + pd.Timedelta(days=HARVEST_SEARCH_DAYS):
            # some fields' post-harvest minimum doesn't dip below the
            # threshold (e.g. quick double-cropping leaves little bare
            # soil) -- fall back to the post-peak trough as the harvest
            # proxy, but only when the full search window was observed
            post_peak = series[(series.index > peak_date) & (series.index <= harvest_search_end)]
            if not post_peak.empty:
                harvest_date = post_peak.idxmin()

        rows.append(
            {
                "season": f"{year}/{str(year + 1)[-2:]}",
                "emergence_date": emergence_date.strftime("%Y-%m-%d"),
                "peak_date": peak_date.strftime("%Y-%m-%d"),
                "harvest_date": harvest_date.strftime("%Y-%m-%d") if harvest_date is not None else None,
            }
        )

    return rows


def main():
    fields = json.loads(FIELDS_PATH.read_text())["features"]
    for feature in fields:
        field_id = feature["properties"]["id"]
        csv_path = DATA_DIR / f"ndvi_{field_id}.csv"
        if not csv_path.exists():
            print(f"{field_id}: {csv_path} not found, skipping")
            continue

        series = load_smooth_series(field_id)
        rows = detect_seasons(series)

        out_path = DATA_DIR / f"phenology_{field_id}.csv"
        pd.DataFrame(rows, columns=["season", "emergence_date", "peak_date", "harvest_date"]).to_csv(
            out_path, index=False
        )
        print(f"{field_id}: {len(rows)} seasons -> {out_path}")
        for r in rows:
            print(f"    {r['season']}: emergence={r['emergence_date']} peak={r['peak_date']} harvest={r['harvest_date']}")


if __name__ == "__main__":
    main()
