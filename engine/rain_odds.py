"""TG.2 — "Rain left in the season" gauge: pure climatology, no forecast.

For every candidate sowing date D (Jan 1 -> Apr 30) and every crop in
data/crops_params.csv, compute the HISTORICAL odds that enough rain falls
during the crop's cycle: over the 27 Jan-Jun half-years 2000-2026, the share
of years where rain accumulated from D through D + cycle_days (capped at
Jun 30, the regional dry season) meets the crop's water need. The need is a
single climatological number per crop: cycle_days x stage-weighted mean Kc x
mean daily ET0 (same radiation-based Hargreaves form as water_balance.py).

Also exports the rainy-season cessation-date distribution: per year, the
first date after Feb 1 whose following 20 days accumulate < 20 mm.

No model, no forecast — these are historical odds only (honest-labeling rule).

Inputs : data/climate_daily.csv, data/crops_params.csv
Outputs: data/rain_odds.csv, data/rain_cessation.csv, web/data/rain_odds.json
         (see docs/CONTRACTS.md)

Usage: python engine/rain_odds.py
"""

import csv
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIMATE = ROOT / "data" / "climate_daily.csv"
CROPS = ROOT / "data" / "crops_params.csv"
OUT_ODDS = ROOT / "data" / "rain_odds.csv"
OUT_CESS = ROOT / "data" / "rain_cessation.csv"
OUT_JSON = ROOT / "web" / "data" / "rain_odds.json"

YEARS = range(2000, 2027)          # 27 complete Jan-Jun half-years
SEASON_END = (6, 30)               # rain after Jun 30 is irrelevant (dry season)
DATE_START = date(2026, 1, 1)      # decision-season axis, matches success_table
DATE_END = date(2026, 4, 30)
STAGE_FRACTIONS = (0.15, 0.35, 0.20, 0.30)  # same split as water_balance.py
CESS_WINDOW_DAYS = 20              # cessation: first date after Feb 1 whose
CESS_THRESHOLD_MM = 20.0           # next 20 days accumulate < 20 mm


def load_climate():
    """date -> (rain_mm, et0_mm) — ET0 identical to water_balance.py."""
    out = {}
    with CLIMATE.open() as f:
        for r in csv.DictReader(f):
            tmin, tmax = float(r["tmin"]), float(r["tmax"])
            rs = float(r["radiation"])
            tmean = (tmin + tmax) / 2.0
            et0 = max(0.0, 0.0135 * (rs / 2.45) * (tmean + 17.8))
            out[date.fromisoformat(r["date"])] = (float(r["rain_mm"]), et0)
    return out


def percentile(sorted_vals, q):
    """Linear-interpolation percentile of a pre-sorted list."""
    if not sorted_vals:
        return None
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def mean_et0_feb_may(climate):
    """Climatological mean daily ET0 over Feb-May (the succession window)."""
    vals = [et0 for d, (_, et0) in climate.items()
            if d.year in YEARS and 2 <= d.month <= 5]
    return sum(vals) / len(vals)


def crop_need_mm(crop, et0_mean):
    kcs = tuple(float(crop[k]) for k in
                ("kc_establishment", "kc_vegetative", "kc_flowering", "kc_filling"))
    kc_mean = sum(f * k for f, k in zip(STAGE_FRACTIONS, kcs))
    return int(crop["cycle_days"]) * kc_mean * et0_mean


def rain_in_window(climate, start, days):
    """Rain accumulated start -> start+days, capped at Jun 30 of start's year."""
    end = min(start + timedelta(days=days), date(start.year, *SEASON_END))
    total = 0.0
    d = start
    while d <= end:
        if d in climate:
            total += climate[d][0]
        d += timedelta(days=1)
    return total


def cessation_date(climate, year):
    """First date after Feb 1 whose following CESS_WINDOW_DAYS sum < threshold."""
    d = date(year, 2, 1)
    stop = date(year, *SEASON_END)
    while d <= stop:
        ahead = sum(climate.get(d + timedelta(days=i), (0.0, 0.0))[0]
                    for i in range(CESS_WINDOW_DAYS))
        if ahead < CESS_THRESHOLD_MM:
            return d
        d += timedelta(days=1)
    return stop


def safe_date(year, md):
    try:
        return md.replace(year=year)
    except ValueError:  # Feb 29 on a non-leap year
        return date(year, 3, 1)


def main():
    climate = load_climate()
    with CROPS.open() as f:
        crops = list(csv.DictReader(f))

    et0_mean = mean_et0_feb_may(climate)
    needs = {c["crop"]: round(crop_need_mm(c, et0_mean)) for c in crops}
    cycles = {c["crop"]: int(c["cycle_days"]) for c in crops}
    print(f"Mean Feb-May ET0: {et0_mean:.2f} mm/day")
    print("Water need (mm):", needs)

    dates, remaining = [], {"p10": [], "p50": [], "p90": []}
    probs = {c["crop"]: [] for c in crops}
    d = DATE_START
    while d <= DATE_END:
        dates.append(d.isoformat())
        rem = sorted(rain_in_window(climate, safe_date(y, d), 365) for y in YEARS)
        for q, key in ((0.1, "p10"), (0.5, "p50"), (0.9, "p90")):
            remaining[key].append(round(percentile(rem, q), 1))
        for c in crops:
            name = c["crop"]
            got = [rain_in_window(climate, safe_date(y, d), cycles[name])
                   for y in YEARS]
            probs[name].append(round(
                sum(1 for g in got if g >= needs[name]) / len(got), 3))
        d += timedelta(days=1)

    cess = {y: cessation_date(climate, y) for y in YEARS}
    cess_sorted = sorted(v.replace(year=2026) for v in cess.values())
    cess_pct = {k: percentile(cess_sorted, q).isoformat()
                for k, q in (("p10", 0.1), ("p50", 0.5), ("p90", 0.9))}

    crop_names = [c["crop"] for c in crops]
    with OUT_ODDS.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "rain_remaining_p10", "rain_remaining_p50",
                    "rain_remaining_p90"] + [f"prob_{c}" for c in crop_names])
        for i, ds in enumerate(dates):
            w.writerow([ds, remaining["p10"][i], remaining["p50"][i],
                        remaining["p90"][i]] + [probs[c][i] for c in crop_names])
    with OUT_CESS.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "cessation_date"])
        for y in sorted(cess):
            w.writerow([y, cess[y].isoformat()])

    OUT_JSON.write_text(json.dumps({
        "n_years": len(list(YEARS)),
        "year_range": "2000-2026",
        "needs_mm": needs,
        "cycle_days": cycles,
        "dates": dates,
        "remaining": remaining,
        "probs": probs,
        "cessation": cess_pct,
    }, separators=(",", ":")), encoding="utf-8")

    print(f"Wrote {OUT_ODDS} ({len(dates)} dates), {OUT_CESS}, {OUT_JSON}")
    print("Cessation p10/p50/p90:", cess_pct)
    print("\nSanity — P(enough rain), selected dates:")
    print(f"{'crop':<12}" + "".join(f"{md:>8}" for md in
          ("01-15", "02-01", "02-15", "03-01", "03-15", "04-01")))
    for c in crop_names:
        row = ""
        for md in ("01-15", "02-01", "02-15", "03-01", "03-15", "04-01"):
            i = dates.index(f"2026-{md}")
            row += f"{probs[c][i]:8.2f}"
        print(f"{c:<12}" + row)


if __name__ == "__main__":
    main()
