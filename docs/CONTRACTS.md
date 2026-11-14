# Data Contracts

This is the single source of truth for every file that crosses a boundary between phases (see [execution-plan.md](execution-plan.md)). If you change a format here, ping the team — whoever consumes the file downstream will break otherwise.

Rule of thumb: **small structured tables (CSV, GeoJSON, JSON) live in `/data` or `/web/data` and ARE committed to git.** Raw satellite rasters (`.tif`, `.nc`, `.hdf5`) are NOT committed — they're intermediate/local only (see `.gitignore`).

All dates are ISO 8601 (`YYYY-MM-DD`). All CSVs are UTF-8, comma-separated, header row included.

---

## Input / reference files

### `data/fields.geojson`
- **Produced by:** T0.3
- **Format:** standard GeoJSON `FeatureCollection`, one `Feature` per field.
- **Required properties per feature:** `id` (e.g. `"T1"`), `name` (free text).

### `data/fields_attributes.csv`
- **Produced by:** TA.3
- **Columns:** `field_id, slope_deg, area_ha`

### `data/crops_params.csv`
- **Produced by:** TC.1
- **Columns:** `crop, cycle_days, kc_establishment, kc_vegetative, kc_flowering, kc_filling, drought_sensitivity, zarc_window_start, zarc_window_end`

### `data/pests.csv`
- **Produced by:** TD.1
- **Columns:** `pest, crop, effect` — `effect` is an integer in `[-2, 2]` (negative = crop favors the pest, positive = crop suppresses it).

---

## Satellite / climate exports (Phase A)

### `data/ndvi_<field_id>.csv`
- **Produced by:** TA.1 — **Consumed by:** TB.1
- **Columns:** `date, ndvi_raw, ndvi_smooth`
- **Notes:** `ndvi_smooth` is added by TB.1, so this file's schema grows after Phase B; until then `ndvi_smooth` may be absent.

### `data/climate_daily.csv`
- **Produced by:** TA.2 — **Consumed by:** TB.3, TC.2
- **Columns:** `date, rain_mm, tmin, tmax, radiation`

---

## Engine 1 — harvest prediction (Phase B)

### `data/phenology_<field_id>.csv`
- **Produced by:** TB.2 — **Consumed by:** TB.3
- **Columns:** `season, emergence_date, peak_date, harvest_date`

### `data/harvest_pred_<field_id>.csv`
- **Produced by:** TB.3 — **Consumed by:** TD.3, `web/data` export (TE.2)
- **Columns:** `p10_date, p50_date, p90_date`

---

## Engine 2 — what fits in the window (Phase C)

### `data/success_table.csv`
- **Produced by:** TC.2 — **Consumed by:** TD.3
- **Columns:** `crop, sowing_date, scenario, success_prob`
- **Notes:** `scenario` ∈ `{nino, nina, neutral}`. `success_prob` ∈ `[0, 1]`.

### `data/bare_soil_<field_id>.csv`
- **Produced by:** TC.3 — **Consumed by:** TD.3
- **Columns:** `strategy, year, bare_days`

---

## Strategies and scoring (Phase D)

### `web/data/strategies.json`
- **Produced by:** TD.2 — **Consumed by:** TE.1 / TE.2 (frontend)
- **Format:** JSON array, one object per strategy:
  ```json
  {
    "id": "corn_brachiaria",
    "name": "Corn + Brachiaria",
    "why": "...",
    "evidence": "...",
    "benefits": ["...", "..."],
    "gaps": ["..."],
    "risks": ["..."],
    "agronomist_notice": "..."
  }
  ```

### Score formula (implemented client-side in JS, not a file)
`score = w1*income + w2*soil_protection + w3*(1 - risk)`, normalized to `0-100`. `w1/w2/w3` come from the farmer's slider inputs (section 6 of `team-guide.md`); `income` derives from crop potential, `soil_protection` from bare-soil days + SRTM erosion + pest effects, `risk` from `success_table.success_prob`.

---

## Frontend data (Phase E)

### `web/data/*.json`
- **Produced by:** TE.2 (one export step that converts the CSVs above into JSON the browser can `fetch` with no server)
- Expected files: `fields.json` (from `fields.geojson` + `fields_attributes.csv`), `harvest_<field_id>.json`, `success_table.json`, `strategies.json`.
- **Rule:** the frontend never reads a `.csv` directly — only JSON under `web/data/`. Keeps TE.1 decoupled from the engine's output format.

---

## Validation (Phase F)

### `data/imea_weekly.csv`
- **Produced by:** manual download from IMEA's public spreadsheet (TF.1)
- **Columns:** `week_start_date, pct_harvested`
