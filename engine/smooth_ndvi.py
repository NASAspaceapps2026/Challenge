"""Field Shift -- TB.1: smooth the NDVI series per field.

Reads data/ndvi_<field_id>.csv (raw, irregular-interval Sentinel-2 + MODIS
mean NDVI, as produced by TA.1), removes isolated spike outliers (cloud
that slipped through the S2/MODIS QA mask), interpolates to a daily step,
and applies a Savitzky-Golay filter to get a clean annual rise-peak-fall
curve. Overwrites each CSV in place, adding the ndvi_smooth column per
docs/CONTRACTS.md.

Run:
    python engine/smooth_ndvi.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

REPO_ROOT = Path(__file__).resolve().parent.parent
FIELDS_PATH = REPO_ROOT / "data" / "fields.geojson"
DATA_DIR = REPO_ROOT / "data"

SAVGOL_WINDOW_DAYS = 31
SAVGOL_POLYORDER = 3

SPIKE_JUMP = 0.25  # NDVI jump to/from a point, each side, to call it a spike
SPIKE_NEIGHBOR_AGREEMENT = 0.15  # how close the two neighbors must be to each other


def remove_spikes(raw: pd.Series) -> pd.Series:
    """Flag isolated single-point spikes: a cloud that slipped through the
    S2/MODIS QA mask crashes NDVI for exactly one observation, with the
    points before and after agreeing closely with each other. Ordinary
    dry-season noise, where neighbors also drift, is left alone."""
    v = raw.to_numpy()
    prev = np.roll(v, 1)
    nxt = np.roll(v, -1)
    jump_prev = np.abs(v - prev)
    jump_next = np.abs(v - nxt)
    neighbors_agree = np.abs(prev - nxt)

    is_spike = (
        (jump_prev > SPIKE_JUMP)
        & (jump_next > SPIKE_JUMP)
        & (neighbors_agree < SPIKE_NEIGHBOR_AGREEMENT)
    )
    is_spike[0] = is_spike[-1] = False  # no two-sided neighbors at the edges

    cleaned = raw.where(~pd.Series(is_spike, index=raw.index))
    return cleaned


def smooth_field(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby("date", as_index=False)["ndvi_raw"].mean().sort_values("date")

    df["ndvi_raw"] = remove_spikes(df["ndvi_raw"])

    daily_index = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    daily = df.set_index("date").reindex(daily_index)
    daily.index.name = "date"

    interpolated = daily["ndvi_raw"].interpolate(method="time").bfill().ffill()

    window = min(SAVGOL_WINDOW_DAYS, len(interpolated))
    if window % 2 == 0:
        window -= 1
    polyorder = min(SAVGOL_POLYORDER, window - 1)
    smoothed = savgol_filter(interpolated.to_numpy(), window, polyorder, mode="interp")

    out = pd.DataFrame(
        {
            "date": daily_index.strftime("%Y-%m-%d"),
            "ndvi_raw": daily["ndvi_raw"].to_numpy(),
            "ndvi_smooth": np.clip(smoothed, 0.0, 1.0).round(4),
        }
    )
    return out


def main():
    fields = json.loads(FIELDS_PATH.read_text())["features"]
    for feature in fields:
        field_id = feature["properties"]["id"]
        csv_path = DATA_DIR / f"ndvi_{field_id}.csv"
        if not csv_path.exists():
            print(f"{field_id}: {csv_path} not found, skipping")
            continue

        out = smooth_field(csv_path)
        out.to_csv(csv_path, index=False)
        n_raw = out["ndvi_raw"].notna().sum()
        print(
            f"{field_id}: {len(out)} daily rows ({n_raw} with raw obs) -> {csv_path}  "
            f"smooth range {out['ndvi_smooth'].min():.2f}-{out['ndvi_smooth'].max():.2f}"
        )


if __name__ == "__main__":
    main()
