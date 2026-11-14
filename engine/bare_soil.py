"""TC.3 — Bare-soil days per field x year x strategy.

Observed bare-soil days = days with daily ndvi_smooth < 0.30 between May 1 and
Sep 30 (the dry season). The satellite only shows what actually happened —
essentially the "current" strategy (solo safrinha corn, field bare after its
harvest). The other strategies cannot be observed, so they are estimated with
simple, explainable rules applied to the observed count:

  current_corn     1.00 x observed  (that's what the satellite saw)
  corn_brachiaria  0.10 x observed  (living brachiaria cover through the dry
                                     season; small residual for establishment)
  sorghum_millet   0.85 x observed  (similar timing to corn, slightly better
                                     residue; still no living cover)
  cover_crotalaria 0.40 x observed  (green cover until desiccation ~Jun-Jul,
                                     then thick residue)

Strategy ids match web/data/strategies.json (TD.2).

Input : data/ndvi_<field>.csv (needs ndvi_smooth, daily — from TB.1)
Output: data/bare_soil_<field>.csv  (strategy, year, bare_days)

Usage: python3 engine/bare_soil.py
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

NDVI_BARE = 0.30
MONTHS = range(5, 10)  # May..Sep
STRATEGY_FACTORS = {
    "current_corn": 1.00,
    "corn_brachiaria": 0.10,
    "sorghum_millet": 0.85,
    "cover_crotalaria": 0.40,
}


def main():
    fields = sorted(p.stem.split("_", 1)[1] for p in DATA.glob("ndvi_T*.csv"))
    for fid in fields:
        observed = {}  # year -> bare days
        with (DATA / f"ndvi_{fid}.csv").open() as f:
            for r in csv.DictReader(f):
                if not r.get("ndvi_smooth"):
                    continue
                year, month = int(r["date"][:4]), int(r["date"][5:7])
                if month in MONTHS and float(r["ndvi_smooth"]) < NDVI_BARE:
                    observed[year] = observed.get(year, 0) + 1
        # keep only years with full May-Sep coverage possible
        out = DATA / f"bare_soil_{fid}.csv"
        with out.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["strategy", "year", "bare_days"])
            for strategy, factor in STRATEGY_FACTORS.items():
                for year in sorted(observed):
                    w.writerow([strategy, year, round(observed[year] * factor)])
        yrs = sorted(observed)
        mean = sum(observed.values()) / len(observed)
        print(f"{fid}: years {yrs[0]}-{yrs[-1]}, observed bare days "
              f"mean {mean:.0f} (min {min(observed.values())}, "
              f"max {max(observed.values())})")


if __name__ == "__main__":
    main()
