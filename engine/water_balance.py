"""TC.2 — Historical crop water balance -> success probability table.

For each crop x sowing date (Jan-Mar, 5-day steps) x historical year (2000-2025),
simulate a daily soil water bucket (capacity 100 mm): rain in, crop demand out
(ET0 via a radiation-based Hargreaves variant x stage Kc). A year "fails" when
mean water stress during the critical (flowering) stage exceeds the crop's
tolerance. Success probability = share of non-failing historical years, overall
and per ENSO scenario (ONI DJF classification, NOAA).

Inputs : data/climate_daily.csv, data/crops_params.csv  (see docs/CONTRACTS.md)
Output : data/success_table.csv  (crop, sowing_date, scenario, success_prob)

Usage: python3 engine/water_balance.py
"""

import csv
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIMATE = ROOT / "data" / "climate_daily.csv"
CROPS = ROOT / "data" / "crops_params.csv"
OUT = ROOT / "data" / "success_table.csv"

TAW_MM = 100.0          # total available water in the root-zone bucket
STRESS_DEPLETION = 0.5  # ETa starts dropping below 50% of TAW
YEARS = range(2000, 2026)
SOWING_STEP_DAYS = 5

# Stage split as fractions of the cycle: establishment/vegetative/flowering/filling
STAGE_FRACTIONS = (0.15, 0.35, 0.20, 0.30)

# NOAA ONI, DJF value of the sowing year (DJF Dec(Y-1)-Feb(Y)). |ONI| < 0.5 = neutral.
ONI_DJF = {
    2000: -1.7, 2001: -0.7, 2002: -0.1, 2003: 0.9, 2004: 0.4, 2005: 0.6,
    2006: -0.9, 2007: 0.7, 2008: -1.6, 2009: -0.8, 2010: 1.5, 2011: -1.4,
    2012: -0.8, 2013: -0.4, 2014: -0.4, 2015: 0.5, 2016: 2.5, 2017: -0.3,
    2018: -0.9, 2019: 0.7, 2020: 0.5, 2021: -1.0, 2022: -1.0, 2023: -0.7,
    2024: 1.8, 2025: -0.6,
}


def scenario_of(year):
    oni = ONI_DJF[year]
    if oni >= 0.5:
        return "nino"
    if oni <= -0.5:
        return "nina"
    return "neutral"


def load_climate():
    """date -> (rain_mm, et0_mm)."""
    out = {}
    with CLIMATE.open() as f:
        for r in csv.DictReader(f):
            tmin, tmax = float(r["tmin"]), float(r["tmax"])
            rs = float(r["radiation"])  # MJ/m2/day (ALLSKY_SFC_SW_DWN)
            tmean = (tmin + tmax) / 2.0
            # Radiation-based ET0 (Hargreaves-Samani form using measured Rs):
            # ET0 = 0.0135 * (Rs / lambda) * (Tmean + 17.8), lambda = 2.45 MJ/kg
            et0 = max(0.0, 0.0135 * (rs / 2.45) * (tmean + 17.8))
            out[date.fromisoformat(r["date"])] = (float(r["rain_mm"]), et0)
    return out


def load_crops():
    with CROPS.open() as f:
        return list(csv.DictReader(f))


def kc_for_day(day_idx, cycle_days, kcs):
    bounds, acc = [], 0.0
    for frac in STAGE_FRACTIONS:
        acc += frac
        bounds.append(acc * cycle_days)
    for stage, b in enumerate(bounds):
        if day_idx < b:
            return kcs[stage], stage
    return kcs[-1], 3


def simulate(climate, sowing, crop):
    """Mean relative stress (1 - ETa/ETc) during flowering; None if data missing."""
    cycle = int(crop["cycle_days"])
    kcs = tuple(float(crop[k]) for k in
                ("kc_establishment", "kc_vegetative", "kc_flowering", "kc_filling"))
    s = TAW_MM  # sown in the rainy season: bucket starts full
    stress_sum, stress_n = 0.0, 0
    for i in range(cycle):
        d = sowing + timedelta(days=i)
        if d not in climate:
            return None
        rain, et0 = climate[d]
        s = min(TAW_MM, s + rain)
        kc, stage = kc_for_day(i, cycle, kcs)
        etc = kc * et0
        avail = min(1.0, s / (STRESS_DEPLETION * TAW_MM))
        eta = etc * avail
        s = max(0.0, s - eta)
        if stage == 2:  # flowering = critical stage
            stress_sum += 0.0 if etc == 0 else 1.0 - eta / etc
            stress_n += 1
    return stress_sum / stress_n if stress_n else 0.0


def main():
    climate = load_climate()
    crops = load_crops()
    rows = []
    for crop in crops:
        tolerance = 0.10 + 0.35 * (1.0 - float(crop["drought_sensitivity"]))
        d0 = date(2026, 1, 1)
        for off in range(0, 90, SOWING_STEP_DAYS):
            sow_2026 = d0 + timedelta(days=off)
            results = {"all": [], "nino": [], "nina": [], "neutral": []}
            for yr in YEARS:
                try:
                    sowing = sow_2026.replace(year=yr)
                except ValueError:  # Feb 29 on non-leap years
                    sowing = date(yr, 3, 1)
                stress = simulate(climate, sowing, crop)
                if stress is None:
                    continue
                ok = 1.0 if stress <= tolerance else 0.0
                results["all"].append(ok)
                results[scenario_of(yr)].append(ok)
            for scen, vals in results.items():
                if vals:
                    rows.append([crop["crop"], sow_2026.isoformat(), scen,
                                 f"{sum(vals) / len(vals):.3f}"])
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["crop", "sowing_date", "scenario", "success_prob"])
        w.writerows(rows)
    print(f"Wrote {OUT} — {len(rows)} rows.")

    # Sanity print: overall success by crop for a few benchmark sowing dates
    probs = {(r[0], r[1], r[2]): float(r[3]) for r in rows}
    print("\nSuccess prob (all years):")
    print(f"{'crop':<12}" + "".join(f"{d:>10}" for d in
          ("01-01", "01-31", "02-15", "03-02", "03-17", "03-27")))
    for crop in crops:
        c = crop["crop"]
        vals = []
        for md in ("01-01", "01-31", "02-15", "03-02", "03-17", "03-27"):
            v = probs.get((c, f"2026-{md}", "all"))
            vals.append("      -" if v is None else f"{v:10.2f}")
        print(f"{c:<12}" + "".join(vals))


if __name__ == "__main__":
    main()
