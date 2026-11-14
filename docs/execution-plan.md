# Field Shift — Task-by-Task Execution Plan

Each task has: **goal**, **how to do it**, **input → output**, and **done-when**. One task's output is the next task's input — respecting the agreed formats (see [CONTRACTS.md](CONTRACTS.md)) is what lets us work in parallel without integration errors.

## Task tracker (check off as you go)

Owners for later phases are intentionally left as **TBD** — assign when that phase starts, based on who's free.

- [ ] T0.1 — Accounts and access — *everyone*
- [x] T0.2 — Repository and data contracts — done
- [x] T0.3 — Choose the demo fields — done (7 fields, see `data/fields.geojson`)
- [ ] TA.1 — Export NDVI series — **Vinicius**
- [ ] TA.2 — Download historical climate — **Leo**
- [ ] TA.3 — Slope per field — **Leo**
- [ ] TB.1 — Smooth the NDVI — **Vinicius**
- [ ] TB.2 — Detect emergence and peak — **Vinicius**
- [ ] TB.3 — Predict the 2025/26 harvest — TBD
- [ ] TC.1 — Parameterize candidate crops — **Illia**
- [ ] TC.2 — Run the historical water balance — **Leo**
- [ ] TC.3 — Bare-soil risk — TBD
- [ ] TD.1 — Pest table — TBD
- [ ] TD.2 — Write the 4+ strategy cards — TBD
- [ ] TD.3 — Scoring function — TBD
- [ ] TE.1 — Page skeleton — **Zé**
- [ ] TE.2 — Connect real data — **Zé**
- [ ] TE.3 — Interactivity — TBD
- [ ] TE.4 — All fields + polish — TBD
- [ ] TF.1 — IMEA validation — TBD
- [ ] TF.2 — Deploy — TBD
- [ ] TF.3 — Submission — *everyone*

---

## PHASE 0 — Setup (before coding, ~1h)

### T0.1 — Accounts and access
- **Goal:** nobody blocked by missing access.
- **How:** confirm everyone has: a Google Earth Engine account (registration approved), a NASA Earthdata account, access to the GitHub repo, and the team's registration on the Space Apps platform.
- **Done when:** every member runs a "hello world" script on GEE and clones the repo.

### T0.2 — Repository and data contracts
- **Goal:** everyone knows where to put and where to find each file.
- **How:** create in the repo: `/data` (exported CSVs), `/engine` (Python scripts), `/web` (site), `/docs`. Write a `CONTRACTS.md` defining the exact format of each CSV (columns, units, names). Examples:
  - `ndvi_<field>.csv`: `date, ndvi_raw, ndvi_smooth`
  - `climate_daily.csv`: `date, rain_mm, tmin, tmax, radiation`
  - `harvest_pred_<field>.csv`: `p10_date, p50_date, p90_date`
  - `success_table.csv`: `crop, sowing_date, scenario(nino/nina/neutral), success_prob`
- **Done when:** `CONTRACTS.md` is committed and everyone has signed off.

### T0.3 — Choose the demo fields
- **Goal:** 5–10 real fields in Sorriso/Lucas do Rio Verde.
- **How:** open GEE or Google Maps satellite view over the region; draw polygons for large fields (>100 ha) that plant soybean every year (check previous years' imagery), without a pivot irrigation system (a pivot shows up as a circle). Vary them: some early planting, some late; some with visible second crop, some without. Save as `fields.geojson`.
- **Done when:** `fields.geojson` is in the repo with 5–10 named polygons (`T1`, `T2`, ...).
- **Done (2026-11-14):** 7 fields selected near Sorriso, MT (see `engine/gee_field_scouting.js` for the GEE scouting script). All >100ha, confirmed rainfed (checked dry-season composite + NDVI history, no field stays green in Jun-Sep). Note: they ended up clustered within ~5km (well under the 20-30km budget) and their NDVI curves are highly synchronized across years — the intended early/late-planting and safrinha/no-safrinha variety isn't clearly visible in this batch. If adding more fields (T8-T10) later, spread them further across the allowed radius to get real variety.

---

## PHASE A — Satellite data (fire EARLY on Day 1, runs unattended)

### TA.1 — Export NDVI series (Sentinel-2 + MODIS)
- **Goal:** the raw material for the harvest engine.
- **How:** a GEE script that, for each polygon in `fields.geojson`: (1) takes Sentinel-2 SR from 2019→today, filters clouds via the SCL/QA band, computes NDVI = (NIR−RED)/(NIR+RED), takes the polygon's spatial mean per date; (2) does the same with MODIS MOD09GQ/MOD13 to fill cloud gaps; (3) exports one CSV per field to Drive. **Fire these exports in the first hour of the event** — they can take hours.
- **Input:** `fields.geojson` → **Output:** `ndvi_<field>.csv` (2019–2026 series).
- **Done when:** CSVs are in `/data` and a quick plot shows the annual soybean "waves".

### TA.2 — Download historical climate (NASA POWER + GPM)
- **Goal:** 25+ years of daily rainfall and temperature for the region.
- **How:** NASA POWER has a simple REST API — a GET on `power.larc.nasa.gov/api/temporal/daily/point` with the region's center lat/lon, 2000–2026, parameters `PRECTOTCORR, T2M_MIN, T2M_MAX, ALLSKY_SFC_SW_DWN`. For rainfall, compare against GPM IMERG (via GEE, monthly mean over the region) and use whichever has better coverage. One center point is enough — climate varies little at the demo's scale.
- **Output:** `climate_daily.csv`.
- **Done when:** CSV has ~9,500 rows, no gaps, and a monthly-rainfall plot shows Mato Grosso's dry/wet pattern.

### TA.3 — Slope per field (SRTM)
- **Goal:** erosion risk per field (NASA flag + soil-health card).
- **How:** in GEE, `ee.Image('USGS/SRTMGL1_003')` → `ee.Terrain.slope()` → mean per polygon. ~20 lines of code.
- **Output:** a `slope_deg` column in a `fields_attributes.csv` table.
- **Done when:** every field has its slope (expected 0–3° in the region; anything >5° becomes an erosion highlight).

---

## PHASE B — Engine 1: harvest prediction

### TB.1 — Smooth the NDVI
- **Goal:** turn the noisy series into a clean curve.
- **How:** in Python (pandas): merge Sentinel-2 and MODIS, remove outliers (isolated sharp drops = cloud that slipped through the filter), interpolate to a daily step, apply a Savitzky–Golay filter (`scipy.signal.savgol_filter`, ~31-day window).
- **Input:** `ndvi_<field>.csv` → **Output:** an `ndvi_smooth` column.
- **Done when:** the plot shows smooth annual curves with a clear rise–peak–fall.

### TB.2 — Detect emergence and peak for each season
- **Goal:** phenological markers for the current soybean crop and past seasons.
- **How:** emergence = date where `ndvi_smooth` crosses ~0.35 rising (after the dry-season minimum); peak = curve maximum in the Oct–Jan window. Run for every year of every field → a history of "emergence → harvest" (past harvest = date where NDVI drops below ~0.35 falling).
- **Output:** `phenology_<field>.csv`: `season, emergence_date, peak_date, harvest_date`.
- **Done when:** the historical dates match the known calendar (planting Sep–Oct, harvest Jan–Feb).

### TB.3 — Predict the 2025/26 harvest (P10/P50/P90)
- **Goal:** the product's key number.
- **How:** a simple, explainable model: the field's own emergence→harvest duration in previous years, adjusted by growing degree-days (sum of `(Tmax+Tmin)/2 − 10°C` since emergence, from `climate_daily.csv`). The distribution of historical durations gives the percentiles: P10/P50/P90. If a field has few years of history, borrow the neighbors' distribution.
- **Output:** `harvest_pred_<field>.csv`.
- **Done when:** in the 2025/26 replay, the P50 "frozen in December" lands within ≤10 days of the actually detected harvest date. **This is the Day 1 checkpoint.**

---

## PHASE C — Engine 2: what fits in the window (parallel to Phase B)

### TC.1 — Parameterize candidate crops
- **Goal:** the numbers that feed the water balance.
- **How:** a table from Embrapa/ZARC: for corn, sorghum, millet, brachiaria, crotalaria → cycle length (days), water need per stage (Kc coefficient per stage: establishment/vegetative/flowering/filling), drought sensitivity at the critical stage, the region's official ZARC sowing window.
- **Output:** `crops_params.csv`.
- **Done when:** reviewed by whoever on the team understands agronomy (plausible values, sources noted).

### TC.2 — Run the historical water balance
- **Goal:** the "odds table" — the heart of the comparison.
- **How:** for each crop × each possible sowing date (Jan–Mar, 5-day steps) × each historical year (2000–2025): simulate a day-by-day soil water reservoir (capacity ~100 mm): rain in, crop demand out (ET0 estimated via Hargreaves from POWER data × stage Kc). If the deficit at the critical stage exceeds the threshold → that year "fails". % of successful years = success probability. Classify each historical year as El Niño/La Niña/neutral (ONI index, public NOAA table) and compute success probability per scenario too.
- **Input:** `climate_daily.csv` + `crops_params.csv` → **Output:** `success_table.csv`.
- **Done when:** the table reproduces common sense: corn until mid-Feb = high chance; March = drops sharply; millet tolerates later sowing than corn. If it doesn't, revisit the parameters.

### TC.3 — Bare-soil risk
- **Goal:** quantify the cost of leaving the field bare.
- **How:** using the smoothed NDVI, count days with `ndvi_smooth < 0.3` between May and September, per field and per year, under each strategy (e.g., corn-only = bare soil after corn harvest Jun–Sep; with brachiaria = near zero).
- **Output:** `bare_soil_<field>.csv`.
- **Done when:** per-strategy numbers are ready to feed into the score.

---

## PHASE D — Strategies and content

### TD.1 — Pest table
- **How:** a short table (Embrapa sources): nematode → crotalaria suppresses, brachiaria reduces, corn hosts; corn leafhopper → breaking the green bridge helps; etc.
- **Output:** `pests.csv` (pest × crop × effect −2..+2).

### TD.2 — Write the 4+ strategy cards
- **Goal:** the deliverable the challenge scores.
- **How:** for each strategy (current/corn, corn+brachiaria, sorghum-millet, cover/crotalaria), write the 5 required fields: **why** (1 sentence), **evidence** (which of our data backs it — e.g., "X-day window + 78% historical success"), **benefits**, **gaps** ("we don't know the local sorghum price"), **risks** ("requires desiccation at the right timing"). Close with the agronomist disclaimer. Text lives in `strategies.json` for the site to consume.
- **Done when:** all 4 cards are reviewed — **they never go on the cut list.**

### TD.3 — Scoring function
- **How:** score = w1·income + w2·soil_protection + w3·(1−risk), where income comes from crop potential, protection comes from bare soil + erosion (SRTM) + pests, risk comes from `success_table`. Weights w1–w3 are the farmer's sliders. Normalize everything 0–100. Implement in plain JS (runs in the browser).
- **Done when:** changing the weights changes the ranking coherently.

---

## PHASE E — The site (starts with mock data Day 1, real data Day 2)

### TE.1 — Page skeleton
- **How:** plain HTML/CSS/JS (no framework, no build step): a Leaflet map with clickable fields → on click: season timeline (NDVI + P10–P50–P90 harvest window) → ranked strategy cards → controls panel. Start with fake data in the contract's format — so the frontend doesn't wait on the engine.
- **Done when:** navigable with fake data.

### TE.2 — Connect real data
- **How:** the engine exports everything as static JSON in `/web/data/`; the site does a local `fetch`. No server.
- **Done when:** 1 real field works end-to-end in the browser (**end of Day 1**).

### TE.3 — Interactivity
- **How:** each control just re-filters already-loaded tables: "harvest slips X days" slider shifts the date and re-queries `success_table`; constraint checkboxes enable/disable cards; weight sliders re-run the score. Everything instant.
- **Done when:** every control from the guide's table (section 6) works.

### TE.4 — All fields + polish
- **How:** run the pipeline for all 5–10 fields, review copy, glossary tooltips, 2025/26 replay mode with a highlight ("in December we said X; it was harvested on Y").

---

## PHASE F — Validation and wrap-up

### TF.1 — IMEA validation
- **How:** sum our per-field predictions into a regional "% harvested per week" curve and plot it against IMEA's public weekly series. A two-line chart on the site/slides.
- **Done when:** the chart is generated (cuttable if time runs out, but it's ~1h of work and is worth a lot in the pitch).

### TF.2 — Deploy
- **How:** GitHub Pages (Settings → Pages → branch main /web). Test on a phone.

### TF.3 — Submission (start 8h before the deadline)
- **How:** feature freeze → 30s video (script: problem → click a field → window → cards → slider → agronomist disclaimer) → project page on the platform (summary, NASA data used: MODIS, POWER, GPM, SRTM + Sentinel-2 partner data) → slides if the local event requires them → **submit 1h before the deadline.**

---

## OPTIONAL (only if everything above is done)
- **"Draw your farm" backend:** FastAPI with an `analyze_field(geojson)` endpoint that runs the same pipeline in fast mode (MODIS + POWER only), deployed on Hugging Face Spaces or Render. The demo never depends on it.

## Cut order (if we fall behind)
backend → IMEA validation → El Niño filter → fewer fields. **Never cut the strategy cards.**
