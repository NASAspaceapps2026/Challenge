"""TE.2 export step — convert the engine's CSVs into JSON under web/data/.

The frontend only ever fetches JSON from web/data/ (see docs/CONTRACTS.md).
Re-run this script whenever any CSV in data/ changes.

Produces:
  web/data/fields.json        GeoJSON FeatureCollection, properties get
                              slope_deg/area_ha merged from fields_attributes.csv
  web/data/ndvi.json          {field_id: [[date, ndvi_smooth], ...]} weekly points
                              from 2022-07-01 on (enough for 4 seasons on screen)
  web/data/phenology.json     {field_id: [{season, emergence, peak, harvest}]}
  web/data/harvest.json       {field_id: {p10, p50, p90, provisional}} — from
                              harvest_pred_<id>.csv if present (TB.3); otherwise a
                              provisional estimate (median historical emergence->
                              harvest duration applied to the current emergence)
                              flagged "provisional": true
  web/data/success_table.json {crop: {scenario: {sowing_date: prob}}}
  web/data/bare_soil.json     {field_id: {strategy: mean_bare_days}}
  web/data/pests.json         rows as-is  [{pest, crop, effect}]
  web/data/crops_params.json  rows as-is

Usage: python3 engine/export_web_data.py
"""

import csv
import json
import statistics
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
WEB = ROOT / "web" / "data"

NDVI_FROM = "2022-07-01"


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def dump(name, obj):
    path = WEB / name
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {path.relative_to(ROOT)}")


def field_ids():
    return sorted(p.stem.split("_", 1)[1] for p in DATA.glob("ndvi_T*.csv"))


def export_fields():
    gj = json.loads((DATA / "fields.geojson").read_text())
    attrs = {r["field_id"]: r for r in read_csv(DATA / "fields_attributes.csv")}
    for feat in gj["features"]:
        a = attrs.get(feat["properties"]["id"])
        if a:
            feat["properties"]["slope_deg"] = float(a["slope_deg"])
            feat["properties"]["area_ha"] = float(a["area_ha"])
    dump("fields.json", gj)


def export_ndvi():
    out = {}
    for fid in field_ids():
        rows = read_csv(DATA / f"ndvi_{fid}.csv")
        series = [
            [r["date"], round(float(r["ndvi_smooth"]), 3)]
            for i, r in enumerate(rows)
            if r.get("ndvi_smooth") and r["date"] >= NDVI_FROM and i % 7 == 0
        ]
        out[fid] = series
    dump("ndvi.json", out)


def export_phenology():
    out = {}
    for fid in field_ids():
        out[fid] = [
            {"season": r["season"], "emergence": r["emergence_date"],
             "peak": r["peak_date"], "harvest": r["harvest_date"]}
            for r in read_csv(DATA / f"phenology_{fid}.csv")
        ]
    dump("phenology.json", out)
    return out


def export_harvest(phenology):
    out = {}
    for fid in field_ids():
        pred = DATA / f"harvest_pred_{fid}.csv"
        if pred.exists():
            r = read_csv(pred)[0]
            out[fid] = {"p10": r["p10_date"], "p50": r["p50_date"],
                        "p90": r["p90_date"], "provisional": False}
            continue
        # Provisional until TB.3 lands: current-season emergence + the field's
        # historical emergence->harvest duration distribution.
        rows = phenology.get(fid, [])
        done = [r for r in rows if r["harvest"] and r["emergence"]]
        current = [r for r in rows if r["emergence"] and not r["harvest"]]
        if not done or not current:
            continue
        durs = sorted(
            (date.fromisoformat(r["harvest"]) - date.fromisoformat(r["emergence"])).days
            for r in done
        )
        emerg = date.fromisoformat(current[-1]["emergence"])
        q = lambda p: durs[min(len(durs) - 1, int(p * len(durs)))]
        out[fid] = {
            "p10": (emerg + timedelta(days=q(0.10))).isoformat(),
            "p50": (emerg + timedelta(days=statistics.median(durs).__int__())).isoformat(),
            "p90": (emerg + timedelta(days=q(0.90))).isoformat(),
            "provisional": True,
        }
    dump("harvest.json", out)


def export_success():
    out = {}
    for r in read_csv(DATA / "success_table.csv"):
        out.setdefault(r["crop"], {}).setdefault(r["scenario"], {})[
            r["sowing_date"]] = float(r["success_prob"])
    dump("success_table.json", out)


def export_bare_soil():
    out = {}
    for fid in field_ids():
        path = DATA / f"bare_soil_{fid}.csv"
        if not path.exists():
            continue
        acc = {}
        for r in read_csv(path):
            acc.setdefault(r["strategy"], []).append(int(r["bare_days"]))
        out[fid] = {s: round(sum(v) / len(v)) for s, v in acc.items()}
    dump("bare_soil.json", out)


def main():
    WEB.mkdir(parents=True, exist_ok=True)
    export_fields()
    export_ndvi()
    phen = export_phenology()
    export_harvest(phen)
    export_success()
    export_bare_soil()
    dump("pests.json", read_csv(DATA / "pests.csv"))
    dump("crops_params.json", read_csv(DATA / "crops_params.csv"))


if __name__ == "__main__":
    main()
