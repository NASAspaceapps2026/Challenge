"""TF.1 - IMEA validation.

Aggregates the per-field harvest predictions (data/harvest_pred_T*.csv, from TB.3)
into a regional "% harvested over time" curve and plots it against IMEA's public
weekly series for Mato Grosso 2025/26 (data/imea_weekly.csv, see docs/imea-notes.md).

Method: each field's harvest date is modeled as Normal(P50, sd) with sd derived
from the P10-P90 spread (P90-P10 = 2*1.2816*sd). The regional curve is the
area-weighted mean of each field's CDF, evaluated daily.

Output: docs/imea_validation.png (two-line chart for the site/slides).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_PNG = ROOT / "docs" / "imea_validation.png"

# Validated 2-series categorical pair (CVD-safe blue/orange)
COLOR_OURS = "#1d4ed8"
COLOR_IMEA = "#c2410c"

Z_P10_P90 = 2 * norm.ppf(0.90)  # P90 - P10 in sd units (~2.563)


def load_fields():
    attrs = pd.read_csv(DATA / "fields_attributes.csv").set_index("field_id")
    fields = []
    for f in sorted(DATA.glob("harvest_pred_T*.csv")):
        fid = f.stem.replace("harvest_pred_", "")
        row = pd.read_csv(f, parse_dates=["p10_date", "p50_date", "p90_date"]).iloc[0]
        sd = (row.p90_date - row.p10_date).days / Z_P10_P90
        fields.append({
            "field_id": fid,
            "p50": row.p50_date,
            "sd": max(sd, 0.5),
            "area_ha": attrs.loc[fid, "area_ha"],
        })
    return fields


def main():
    fields = load_fields()
    imea = pd.read_csv(DATA / "imea_weekly.csv", parse_dates=["week_start_date"])

    days = pd.date_range("2025-12-20", "2026-03-27", freq="D")
    t = days.values.astype("datetime64[D]").astype(float)
    total_area = sum(f["area_ha"] for f in fields)
    ours = np.zeros(len(days))
    for f in fields:
        mu = np.datetime64(f["p50"], "D").astype(float)
        ours += (f["area_ha"] / total_area) * norm.cdf(t, loc=mu, scale=f["sd"])
    ours *= 100.0

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.plot(days, ours, color=COLOR_OURS, lw=2,
            label="Our 7 fields - predicted (area-weighted, Sorriso MT)")
    ax.plot(imea.week_start_date, imea.pct_harvested, color=COLOR_IMEA, lw=2,
            marker="o", ms=5, label="IMEA weekly bulletin - Mato Grosso state")

    ax.set_ylabel("% of soybean area harvested")
    ax.set_title("2025/26 harvest progress: our prediction vs IMEA (Mato Grosso)")
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.25, lw=0.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    fig.autofmt_xdate()
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG)

    # Console summary: dates at which each curve crosses 50%
    cross_ours = days[np.searchsorted(ours, 50.0)]
    imea_i = np.searchsorted(imea.pct_harvested.values, 50.0)
    lo, hi = imea.iloc[imea_i - 1], imea.iloc[imea_i]
    frac = (50.0 - lo.pct_harvested) / (hi.pct_harvested - lo.pct_harvested)
    cross_imea = lo.week_start_date + frac * (hi.week_start_date - lo.week_start_date)
    print(f"50% crossed: ours {cross_ours.date()} | IMEA (state) {cross_imea.date()} "
          f"| lead {(cross_imea - cross_ours).days}d (Sorriso harvests early - expected ahead)")
    print(f"Chart written to {OUT_PNG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
