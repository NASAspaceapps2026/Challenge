"""Field Shift -- TG.1: recurrent low-vigor spots per field.

Flags in-field zones whose NDVI is anomalously low IN THE SAME PLACE across
multiple seasons -- the signature of a persistent soil problem (nematode
reboleiras, compaction, fertility gaps), as opposed to one-off noise
(cloud, planting failure).

Method (see docs/execution-plan.md, TG.1):
  1. For each of the last 5 seasons, build a per-pixel max-NDVI composite
     (Sentinel-2, 10 m) over a ~7-week peak window centred on mid-January;
     the max over a long window rides over cloud gaps.
  2. Per season, z-score each pixel against its OWN field's mean/stddev --
     removes the good-year/bad-year effect.
  3. Count, per pixel, the seasons with z < -1.
  4. Vectorize pixels low in >= MIN_SEASONS seasons; drop slivers < MIN_AREA_HA.

Honest labeling is binding: this is never "disease detected" -- the frontend
must present it as "recurrent low-vigor zone, pattern consistent with a soil
problem; recommendation: targeted soil sampling here".

Outputs:
  data/spots_<field_id>.geojson   one FeatureCollection per field
  web/data/spots.json             all fields merged, fetched by the frontend

Run (same setup as gee_ndvi_export.py):
    python engine/low_vigor_spots.py
"""

import json
from pathlib import Path

import ee

GEE_PROJECT = "nasaspaceapps-514721"

REPO_ROOT = Path(__file__).resolve().parent.parent
FIELDS_PATH = REPO_ROOT / "data" / "fields.geojson"
DATA_DIR = REPO_ROOT / "data"
WEB_DATA_DIR = REPO_ROOT / "web" / "data"

# Peak-vigor windows: mid-January +/- ~3.5 weeks, one per season.
# Season label "2021/22" = soybean sown ~Oct 2021, peak Jan 2022.
SEASONS = [
    ("2021/22", "2021-12-20", "2022-02-10"),
    ("2022/23", "2022-12-20", "2023-02-10"),
    ("2023/24", "2023-12-20", "2024-02-10"),
    ("2024/25", "2024-12-20", "2025-02-10"),
    ("2025/26", "2025-12-20", "2026-02-10"),
]

Z_THRESHOLD = -1.0   # pixel counts as "low" when z < -1 within its field
MIN_SEASONS = 3      # recurrent = low in >= 3 seasons
MIN_AREA_HA = 0.2    # drop vector slivers smaller than this
SCALE = 10           # Sentinel-2 NDVI resolution (m)


def mask_s2(image):
    scl = image.select("SCL")
    # keep vegetation(4), bare soil(5), water(6), unclassified(7)
    mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
    return image.updateMask(mask)


def peak_ndvi_composite(geom, start, end):
    """Per-pixel max NDVI over the window; None-safe (may be fully masked)."""
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geom)
        .filterDate(start, end)
        .map(mask_s2)
        .map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("ndvi"))
    )
    return col.max().clip(geom)


def season_low_mask(geom, start, end):
    """1 where the pixel's peak NDVI is > |Z_THRESHOLD| sigma below the
    field mean for that season, 0 where it is not, masked where no data."""
    comp = peak_ndvi_composite(geom, start, end)
    stats = comp.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=geom,
        scale=SCALE,
        maxPixels=1e9,
    )
    mean = ee.Number(stats.get("ndvi_mean"))
    std = ee.Number(stats.get("ndvi_stdDev")).max(1e-4)
    z = comp.subtract(ee.Image.constant(mean)).divide(ee.Image.constant(std))
    return z.lt(Z_THRESHOLD).rename("low")


def field_spots(field_id, geom):
    """Vectorized recurrent-low zones for one field -> list of GeoJSON features."""
    low_masks = [season_low_mask(geom, s, e) for _, s, e in SEASONS]
    low_count = ee.ImageCollection(low_masks).sum().rename("seasons_low")
    valid_count = ee.ImageCollection(
        [m.mask().rename("valid") for m in low_masks]
    ).sum()

    recurrent = low_count.gte(MIN_SEASONS)
    vectors = (
        low_count.updateMask(recurrent)
        .toInt()
        .reduceToVectors(
            geometry=geom,
            scale=SCALE,
            geometryType="polygon",
            eightConnected=True,
            labelProperty="seasons_low",
            maxPixels=1e9,
        )
    )

    def enrich(feat):
        area_ha = feat.geometry().area(maxError=1).divide(10000)
        n_valid = valid_count.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=feat.geometry(),
            scale=SCALE, maxPixels=1e9,
        ).get("valid")
        return feat.set(
            {
                "field_id": field_id,
                "area_ha": area_ha,
                "n_seasons": ee.Number(n_valid).round(),
            }
        )

    vectors = vectors.map(enrich).filter(
        ee.Filter.gte("area_ha", MIN_AREA_HA)
    )
    features = vectors.getInfo()["features"]
    # round noisy floats for a small committed file
    for f in features:
        p = f["properties"]
        p["area_ha"] = round(float(p["area_ha"]), 2)
        p["seasons_low"] = int(p["seasons_low"])
        p["n_seasons"] = int(p["n_seasons"])
    return features


def main():
    ee.Initialize(project=GEE_PROJECT)
    fields_fc = json.loads(FIELDS_PATH.read_text())

    all_features = []
    for feature in fields_fc["features"]:
        field_id = feature["properties"]["id"]
        geom = ee.Geometry(feature["geometry"])
        feats = field_spots(field_id, geom)
        print(f"{field_id}: {len(feats)} recurrent low-vigor zone(s)")

        fc = {"type": "FeatureCollection", "features": feats}
        out = DATA_DIR / f"spots_{field_id}.geojson"
        out.write_text(json.dumps(fc), encoding="utf-8")
        all_features.extend(feats)

    web_out = WEB_DATA_DIR / "spots.json"
    web_out.write_text(
        json.dumps({"type": "FeatureCollection", "features": all_features}),
        encoding="utf-8",
    )
    print(f"total: {len(all_features)} zones -> {web_out}")


if __name__ == "__main__":
    main()
