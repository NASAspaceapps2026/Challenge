"""Field Shift -- TA.1: export NDVI series per field (Sentinel-2 + MODIS).

Python port of gee_ndvi_export.js. Reads data/fields.geojson directly (no
coordinates pasted by hand), pulls the NDVI series straight from Earth
Engine via the API, and writes data/ndvi_<field_id>.csv locally -- no
Drive export / manual download step.

One-time setup (per machine):
    pip install earthengine-api pandas
    earthengine authenticate      # opens a browser once, stores a token
Then set GEE_PROJECT below to a Google Cloud project you've registered
for Earth Engine (console.cloud.google.com -> any project id works, it
just needs the Earth Engine API enabled once).

Run:
    python engine/gee_ndvi_export.py
"""

import json
from pathlib import Path

import ee
import pandas as pd

GEE_PROJECT = "nasaspaceapps-514721"

REPO_ROOT = Path(__file__).resolve().parent.parent
FIELDS_PATH = REPO_ROOT / "data" / "fields.geojson"
DATA_DIR = REPO_ROOT / "data"

START_DATE = "2019-01-01"
END_DATE = pd.Timestamp.today().strftime("%Y-%m-%d")


def mask_s2(image):
    scl = image.select("SCL")
    # keep vegetation(4), bare soil(5), water(6), unclassified(7) -- drop clouds/shadow/snow
    mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
    return image.updateMask(mask).divide(10000).copyProperties(
        image, ["system:time_start"]
    )


def s2_ndvi_series(geom):
    col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geom)
        .filterDate(START_DATE, END_DATE)
        .map(mask_s2)
        .map(
            lambda img: img.normalizedDifference(["B8", "B4"])
            .rename("ndvi")
            .copyProperties(img, ["system:time_start"])
        )
    )

    def to_feature(img):
        img = ee.Image(img)
        stat = img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=10, maxPixels=1e9
        )
        return ee.Feature(
            None,
            {"date": img.date().format("YYYY-MM-dd"), "ndvi_raw": stat.get("ndvi")},
        )

    return col.map(to_feature).filter(ee.Filter.notNull(["ndvi_raw"]))


def modis_ndvi_series(geom):
    col = ee.ImageCollection("MODIS/061/MOD13Q1").filterBounds(geom).filterDate(
        START_DATE, END_DATE
    )

    def clean(img):
        good = img.select("SummaryQA").lte(1)  # 0 good, 1 marginal
        ndvi = img.select("NDVI").multiply(0.0001).updateMask(good).rename("ndvi")
        return ndvi.copyProperties(img, ["system:time_start"])

    col = col.map(clean)

    def to_feature(img):
        img = ee.Image(img)
        stat = img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=250, maxPixels=1e9
        )
        return ee.Feature(
            None,
            {"date": img.date().format("YYYY-MM-dd"), "ndvi_raw": stat.get("ndvi")},
        )

    return col.map(to_feature).filter(ee.Filter.notNull(["ndvi_raw"]))


def export_field(field_id, geom):
    merged = s2_ndvi_series(geom).merge(modis_ndvi_series(geom)).sort("date")

    try:
        features = merged.getInfo()["features"]
    except ee.EEException as e:
        print(
            f"{field_id}: getInfo() failed ({e}). Collection may be too large for a "
            "synchronous call -- fall back to Export.table.toDrive like the .js version."
        )
        raise

    rows = [f["properties"] for f in features]
    df = pd.DataFrame(rows, columns=["date", "ndvi_raw"]).drop_duplicates("date")
    df = df.sort_values("date")

    out_path = DATA_DIR / f"ndvi_{field_id}.csv"
    df.to_csv(out_path, index=False)
    print(f"{field_id}: {len(df)} rows -> {out_path}")
    return df


def main():
    ee.Initialize(project=GEE_PROJECT)

    fields_fc = json.loads(FIELDS_PATH.read_text())
    for feature in fields_fc["features"]:
        field_id = feature["properties"]["id"]
        geom = ee.Geometry(feature["geometry"])
        df = export_field(field_id, geom)

        # quick sanity check before moving to the next field: rainfed soybean
        # should look bare (~0.2-0.3) Apr-Sep, rise ~Oct, peak Dec-Jan, drop Feb
        print(
            f"  ndvi_raw range: {df['ndvi_raw'].min():.2f}-{df['ndvi_raw'].max():.2f}"
        )


if __name__ == "__main__":
    main()
