"""Field Shift -- TA.3: slope (SRTM) + area per field -> data/fields_attributes.csv

Python port of gee_slope_export.js so the whole pipeline reruns without the
GEE Code Editor. Columns per docs/CONTRACTS.md: field_id, slope_deg, area_ha.

Run (same setup as gee_ndvi_export.py):
    python engine/slope_attributes.py
"""

import json
from pathlib import Path

import ee

GEE_PROJECT = "nasaspaceapps-514721"

REPO_ROOT = Path(__file__).resolve().parent.parent
FIELDS_PATH = REPO_ROOT / "data" / "fields.geojson"
OUT_PATH = REPO_ROOT / "data" / "fields_attributes.csv"


def main():
    ee.Initialize(project=GEE_PROJECT)
    fields_fc = json.loads(FIELDS_PATH.read_text(encoding="utf-8"))
    slope = ee.Terrain.slope(ee.Image("USGS/SRTMGL1_003"))

    lines = ["field_id,slope_deg,area_ha"]
    for feature in fields_fc["features"]:
        field_id = feature["properties"]["id"]
        geom = ee.Geometry(feature["geometry"])
        mean_slope = slope.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=30
        ).get("slope")
        area_ha = geom.area(maxError=1).divide(10000)
        s, a = ee.List([mean_slope, area_ha]).getInfo()
        lines.append(f"{field_id},{s:.2f},{a:.1f}")
        print(lines[-1])

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {OUT_PATH}")


if __name__ == "__main__":
    main()
