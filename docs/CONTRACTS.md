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
- **Notes:** `ndvi_smooth` is added by TB.1, so this file's schema grows after Phase B; until then `ndvi_smooth` may be absent. **After TB.1, `date` becomes a full daily series** (2019-01-01 → latest available date, one row per day, no gaps) instead of the irregular satellite-pass dates TA.1 produced — needed so TB.2's threshold-crossing detection and later growing-degree-day sums (TB.3) can walk the series day by day. `ndvi_raw` is left blank on days with no actual satellite observation; `ndvi_smooth` is filled for every day (Savitzky-Golay over the linearly time-interpolated raw series, with isolated single-point cloud-slip spikes dropped first).

### `data/climate_daily.csv`
- **Produced by:** TA.2 — **Consumed by:** TB.3, TC.2
- **Columns:** `date, rain_mm, tmin, tmax, radiation`

---

## Engine 1 — harvest prediction (Phase B)

### `data/phenology_<field_id>.csv`
- **Produced by:** TB.2 — **Consumed by:** TB.3
- **Columns:** `season, emergence_date, peak_date, harvest_date`
- **Notes:** `season` is `YYYY/YY` (e.g. `2024/25`, Sep–Oct YYYY planting → Jan–Feb YY harvest). One row per field per season, oldest first, including the most recent (possibly still-growing) season. `peak_date`/`harvest_date` are blank when that stage hasn't happened yet in the data (season in progress) — `emergence_date` is never blank for a row that exists.

### `data/harvest_pred_<field_id>.csv`
- **Produced by:** TB.3 — **Consumed by:** TD.3, `web/data` export (TE.2)
- **Columns:** `p10_date, p50_date, p90_date`

---

## Engine 2 — what fits in the window (Phase C)

### `data/success_table.csv`
- **Produced by:** TC.2 — **Consumed by:** TD.3
- **Columns:** `crop, sowing_date, scenario, success_prob`
- **Notes:** `scenario` ∈ `{all, nino, nina, neutral}` (`all` = every historical year — the frontend's default before the farmer picks an ENSO filter). `success_prob` ∈ `[0, 1]`. `sowing_date` uses year **2026** (the decision season), Jan 1 → Mar 27 in 5-day steps.

### `data/bare_soil_<field_id>.csv`
- **Produced by:** TC.3 — **Consumed by:** TD.3
- **Columns:** `strategy, year, bare_days`
- **Notes:** `strategy` ∈ `{current_corn, corn_brachiaria, sorghum_millet, cover_crotalaria}` — these ids are canonical and must match the `id` field in `web/data/strategies.json` (TD.2). Observed years 2019–2026; only `current_corn` is directly observed, the others are rule-based estimates (see `engine/bare_soil.py`).

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

### `data/spots_<field_id>.geojson` / `web/data/spots.json`
- **Produced by:** TG.1 (`engine/low_vigor_spots.py`)
- **Format:** GeoJSON `FeatureCollection` of recurrent low-vigor zone polygons. `spots.json` is all fields merged into one collection.
- **Properties per feature:** `field_id` (e.g. `"T2"`), `seasons_low` (int, seasons with NDVI z < −1 at this spot), `n_seasons` (int, seasons with valid data, currently 5: 2021/22–2025/26), `area_ha` (float, 2 decimals).
- **Consumed by:** the Leaflet map (red dashed overlay) and the scoring (`recurrentSpots: true` gives `cover_crotalaria` a +8 bonus).
- **Honest labeling (binding):** never present as "disease detected" — always "recurrent low-vigor zone, pattern consistent with a soil problem; recommendation: targeted soil sampling".

### `data/rain_odds.csv` / `data/rain_cessation.csv` / `web/data/rain_odds.json`
- **Produced by:** TG.2 (`engine/rain_odds.py`) — pure climatology from `climate_daily.csv` (2000–2026, 27 Jan–Jun half-years). **No forecast** — honest labeling is binding: always "historical odds".
- **ENSO split (TG.8):** every number is computed pooled (`all`) **and** per ENSO scenario (`nina` / `nino` / `neutral`), reusing `ONI_DJF` + `scenario_of()` imported from `engine/water_balance.py` — do **not** duplicate the ONI table, so the gauge and `success_table.csv` split the history by the same criterion. `ONI_DJF` covers 2000–2025, so **2026 counts only toward `all`**. Resulting n: `all` 27, `nina` 12, `nino` 9, `neutral` 5.
- **`rain_odds.csv` columns:** `date, scenario, n_years, rain_remaining_p10, rain_remaining_p50, rain_remaining_p90, prob_corn, prob_sorghum, prob_millet, prob_brachiaria, prob_crotalaria`
  - `date`: 2026-01-01 → 2026-04-30, daily (decision-season axis, same convention as `success_table.csv`).
  - `scenario`: `all` | `nina` | `nino` | `neutral` — **one row per date × scenario** (480 rows).
  - `n_years`: number of historical years in that scenario (constant per scenario).
  - `rain_remaining_*`: percentiles (mm) of historical rain accumulated from `date` to Jun 30.
  - `prob_<crop>`: share of that scenario's years in which rain accumulated during the crop's cycle (`date` → `date + cycle_days`, capped at Jun 30) met the crop's water need. Need = `cycle_days × stage-weighted mean Kc × mean Feb–May ET0` (same ET0 form as `water_balance.py`), from `crops_params.csv`.
- **`rain_cessation.csv` columns:** `year, scenario, cessation_date` — per year, its ENSO scenario (empty for 2026, unclassified) and the first date after Feb 1 whose following 20 days accumulate < 20 mm.
- **`rain_odds.json`:** `{ n_years, year_range, scenario_n: {scenario: n}, scenario_years: {scenario: [years]}, min_scenario_years, needs_mm: {crop: mm}, cycle_days: {crop: d}, dates: [...], remaining: {scenario: {p10/p50/p90: [...]}}, probs: {scenario: {crop: [...]}}, cessation: {scenario: {p10/p50/p90: date}} }` — arrays parallel to `dates`. Note `remaining`, `probs` and `cessation` are **keyed by scenario first**.
- **Consumed by:** the "rain left in the season" gauge in `web/index.html`, which re-reads it at the sowing date implied by the slip slider **and at the scenario chosen in the Climate scenario selector** (the same control that feeds the strategy cards).
- **Small-sample rule (binding):** `min_scenario_years` (8) is the floor for drawing a curve. Below it (`neutral`, n=5) the frontend shows the raw per-crop shares plus an insufficient-sample notice instead of a polyline. Never smooth or interpolate a scenario curve to make it look nicer — with n=9 the ~11% steps are honest; the fix is labelling the n on screen.

### `data/productivity_<field_id>.csv` / `web/data/productivity.json`
- **Produced by:** TG.3 (`engine/productivity.py`) from `ndvi_<field>.csv` + `phenology_<field>.csv`.
- **CSV columns:** `season, emergence_date, harvest_date, ndvi_integral, n_days, complete, deviation_pct`
  - `ndvi_integral`: sum of daily `ndvi_smooth` from `emergence_date` to `harvest_date` inclusive (biomass proxy).
  - `n_days`: number of daily values summed.
  - `complete`: `true`/`false` — a season without a `harvest_date` (still in the field) gets **no partial integral**: `ndvi_integral`, `n_days`, `deviation_pct` empty.
  - `deviation_pct`: 100 × (integral − field mean over complete seasons) / mean, 1 decimal.
- **`productivity.json`:** `{ "<field_id>": { mean_integral, n_seasons, seasons: [{season, ndvi_integral, n_days, complete, deviation_pct}] } }` — incomplete seasons have `null` in the numeric fields.
- **Consumed by:** the "relative productivity" box on the field panel in `web/index.html` (2025/26 highlighted vs the field's own mean), and TG.4 (per-field yield calibration) as input.
- **Honest labeling (binding):** RELATIVE signal only — never convert to sacas/ha here; that requires farmer-entered calibration (TG.4).

---

## Validation (Phase F)

### `data/imea_weekly.csv`
- **Produced by:** manual download from IMEA's public spreadsheet (TF.1)
- **Columns:** `week_start_date, pct_harvested`
