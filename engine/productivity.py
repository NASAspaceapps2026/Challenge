"""TG.3 — Relative productivity per field.

Seasonal NDVI integral (sum of daily ndvi_smooth between emergence and
harvest) per season per field, and % deviation from the field's own
multi-season mean. RELATIVE signal only — never converted to sacas/ha
(that calibration is TG.4's job, which consumes this output).

Reads:  data/ndvi_T*.csv, data/phenology_T*.csv
Writes: data/productivity_T*.csv, web/data/productivity.json
"""

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web", "data")

with open(os.path.join(DATA, "fields.geojson"), encoding="utf-8") as _f:
    FIELDS = [feat["properties"]["id"] for feat in json.load(_f)["features"]]


def load_ndvi(field):
    """date -> ndvi_smooth (float)."""
    out = {}
    with open(os.path.join(DATA, f"ndvi_{field}.csv"), newline="") as f:
        for row in csv.DictReader(f):
            v = row.get("ndvi_smooth", "").strip()
            if v:
                out[row["date"]] = float(v)
    return out


def run_field(field):
    ndvi = load_ndvi(field)
    dates = sorted(ndvi)
    rows = []
    with open(os.path.join(DATA, f"phenology_{field}.csv"), newline="") as f:
        for row in csv.DictReader(f):
            season = row["season"]
            emu = row["emergence_date"].strip()
            har = row["harvest_date"].strip()
            if not emu or not har:
                # in-progress season: no partial integral (by design)
                rows.append({"season": season, "emergence_date": emu,
                             "harvest_date": har, "ndvi_integral": "",
                             "n_days": "", "complete": "false",
                             "deviation_pct": ""})
                continue
            vals = [ndvi[d] for d in dates if emu <= d <= har]
            integral = sum(vals)
            rows.append({"season": season, "emergence_date": emu,
                         "harvest_date": har,
                         "ndvi_integral": round(integral, 2),
                         "n_days": len(vals), "complete": "true",
                         "deviation_pct": None})  # filled below

    complete = [r for r in rows if r["complete"] == "true"]
    mean = sum(r["ndvi_integral"] for r in complete) / len(complete)
    for r in complete:
        r["deviation_pct"] = round(100 * (r["ndvi_integral"] - mean) / mean, 1)

    path = os.path.join(DATA, f"productivity_{field}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["season", "emergence_date",
                                          "harvest_date", "ndvi_integral",
                                          "n_days", "complete",
                                          "deviation_pct"])
        w.writeheader()
        w.writerows(rows)
    print(f"{field}: {len(complete)} complete seasons, mean integral "
          f"{mean:.1f} -> {path}")

    return {
        "mean_integral": round(mean, 2),
        "n_seasons": len(complete),
        "seasons": [
            {"season": r["season"],
             "ndvi_integral": r["ndvi_integral"] if r["complete"] == "true" else None,
             "n_days": r["n_days"] if r["complete"] == "true" else None,
             "complete": r["complete"] == "true",
             "deviation_pct": r["deviation_pct"] if r["complete"] == "true" else None}
            for r in rows
        ],
    }


def main():
    out = {}
    for field in FIELDS:
        out[field] = run_field(field)
    os.makedirs(WEB, exist_ok=True)
    dst = os.path.join(WEB, "productivity.json")
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
