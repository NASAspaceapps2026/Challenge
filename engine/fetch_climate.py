"""TA.2 — Download daily climate from NASA POWER for the demo region.

Produces data/climate_daily.csv per docs/CONTRACTS.md:
    date, rain_mm, tmin, tmax, radiation

One point at the centroid of data/fields.geojson is enough — climate varies
little at the demo's scale. POWER serves 2000->near-present with a few days
of latency; missing values (-999) at the tail are dropped.

Usage: python3 engine/fetch_climate.py
"""

import csv
import json
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ROOT / "data" / "fields.geojson"
OUT = ROOT / "data" / "climate_daily.csv"

PARAMS = "PRECTOTCORR,T2M_MIN,T2M_MAX,ALLSKY_SFC_SW_DWN"
START = "20000101"
FILL = -999.0


def centroid():
    gj = json.loads(FIELDS.read_text())
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            for k in c:
                walk(k)

    for feat in gj["features"]:
        walk(feat["geometry"]["coordinates"])
    return sum(ys) / len(ys), sum(xs) / len(xs)  # lat, lon


def main():
    lat, lon = centroid()
    end = date.today().strftime("%Y%m%d")
    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters={PARAMS}&community=AG&latitude={lat:.4f}&longitude={lon:.4f}"
        f"&start={START}&end={end}&format=JSON"
    )
    print(f"Fetching POWER daily {START}->{end} at ({lat:.4f}, {lon:.4f}) ...")
    with urllib.request.urlopen(url, timeout=300) as r:
        data = json.load(r)

    p = data["properties"]["parameter"]
    rain = p["PRECTOTCORR"]
    tmin = p["T2M_MIN"]
    tmax = p["T2M_MAX"]
    rad = p["ALLSKY_SFC_SW_DWN"]

    keys = sorted(rain)
    series = []
    for key in keys:
        vals = [rain[key], tmin[key], tmax[key], rad[key]]
        vals = [None if v is None or float(v) == FILL else float(v) for v in vals]
        series.append((key, vals))

    # drop trailing days where everything is still missing (POWER latency)
    while series and all(v is None for v in series[-1][1]):
        series.pop()

    # linearly interpolate isolated interior gaps per parameter
    filled = 0
    for col in range(4):
        last = None
        for i, (_, vals) in enumerate(series):
            if vals[col] is not None:
                if last is not None and i - last > 1:
                    a, b = series[last][1][col], vals[col]
                    for j in range(last + 1, i):
                        series[j][1][col] = a + (b - a) * (j - last) / (i - last)
                        filled += 1
                last = i

    rows = []
    for key, vals in series:
        if any(v is None for v in vals):
            continue  # leading gap with no left neighbor — drop
        d = datetime.strptime(key, "%Y%m%d").strftime("%Y-%m-%d")
        rows.append([d] + [f"{v:.2f}" for v in vals])

    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "rain_mm", "tmin", "tmax", "radiation"])
        w.writerows(rows)

    print(f"Wrote {OUT} — {len(rows)} rows ({rows[0][0]} -> {rows[-1][0]}), "
          f"{filled} values interpolated.")

    # sanity: monthly rainfall climatology should show MT's wet/dry pattern
    monthly = [0.0] * 12
    years = len({r[0][:4] for r in rows})
    for r in rows:
        monthly[int(r[0][5:7]) - 1] += float(r[1])
    print("Mean monthly rain (mm):",
          " ".join(f"{m}:{monthly[m-1]/years:.0f}" for m in range(1, 13)))


if __name__ == "__main__":
    sys.exit(main())
