# Field Shift — Task-by-Task Execution Plan

Each task has: **goal**, **how to do it**, **input → output**, and **done-when**. One task's output is the next task's input — respecting the agreed formats (see [CONTRACTS.md](CONTRACTS.md)) is what lets us work in parallel without integration errors.

## Quick start — read your own section, then go

No need to read the whole plan first. Find your name below, do that task (full details further down this file), commit and push when done.

**Vinicius — TA.1, then TB.1 + TB.2**
- What: export the NDVI satellite series per field, then clean it into a smooth curve and detect emergence/harvest dates.
- How: Google Earth Engine (script fired early, takes hours to run) for the export; Python (pandas + scipy's `savgol_filter`) for the smoothing/detection.
- Output: `data/ndvi_<field>.csv` → `data/phenology_<field>.csv`.
- **Round 2 (assigned 2026-11-14, Round 1 done):** TB.3 → TF.1 → TD.2 → TE.4 → TF.2. Follows the harvest-prediction chain: TB.3 consumes `phenology_<field>.csv`; TF.1 (IMEA validation) and TE.4's 2025/26 replay mode both consume TB.3's `harvest_pred_<field>.csv`. TD.2 (strategy cards) is the deliverable that's never cut, so start it as soon as TB.3 is done.

**Leo — TA.2, TA.3, then TC.2**
- What: pull 25+ years of daily rainfall/temperature, get each field's slope, then simulate the water balance for every candidate crop.
- How: NASA POWER REST API (simple GET request) for climate; Google Earth Engine (SRTM, ~20 lines) for slope; Python for the day-by-day water balance simulation.
- Output: `data/climate_daily.csv`, `data/fields_attributes.csv` → `data/success_table.csv`.
- **Round 2 (assigned 2026-11-14, Round 1 done, plus TC.1):** TC.3 → TD.1 → TD.3 → TE.3. Follows the strategy-scoring chain: TC.3 reads the daily `ndvi_smooth` (ready now); TD.3's score combines `success_table.csv`, `bare_soil_<field>.csv` and `pests.csv`, all from this chain; TE.3's sliders re-run that score. TE.3 is in `web/`, which is Zé's area, so agree with him on where the scoring JS plugs in.

**Illia — TC.1**
- What: fill one row per candidate crop (corn, sorghum, millet, brachiaria, crotalaria) in `data/crops_params.csv`, with these columns:
  - `cycle_days` — how many days from sowing to harvest/cutting for that crop. Easy to find, any agronomy source states it (e.g. safrinha corn ≈ 110–150 days).
  - `kc_establishment / kc_vegetative / kc_flowering / kc_filling` — the crop's water-use coefficient (Kc) at each of its 4 growth stages. Kc is just "how much water the crop pulls compared to a reference grass" (Kc=1 means same as reference) — used later to run the water balance. **Source: FAO Irrigation & Drainage Paper 56** (Allen et al. 1998) — it has standard Kc tables per crop/stage. Search "FAO 56 crop coefficient corn/sorghum/millet" — tables are public and widely reproduced online. For brachiaria/crotalaria (not in FAO-56) use Embrapa pasture/cover-crop bulletins, or if nothing specific exists, a reasonable pasture-grass approximation is fine — just note it.
  - `drought_sensitivity` — a single number saying how badly this crop suffers if water runs short *during its most critical stage* (for corn/sorghum that's flowering; this is well documented agronomically). No fixed scale is defined yet — pick something simple like 0–1 (0 = tolerant, 1 = very sensitive) and use it consistently across all 5 crops; corn should come out higher than sorghum/millet (known to be more drought-tolerant), that's the sanity check.
  - `zarc_window_start / zarc_window_end` — the official recommended sowing window for Mato Grosso. **Source: ZARC — Zoneamento Agrícola de Risco Climático**, published by MAPA (Ministério da Agricultura). Portal: search "ZARC Mato Grosso" + the crop name (e.g. "ZARC milho safrinha Mato Grosso") — it's a government table by municipality/crop/cycle/soil type. Use Sorriso or Lucas do Rio Verde as the reference municipality.
- How: pure research — no coding, no GEE, no waiting. Can be done entirely on his own laptop right now, in a spreadsheet, then saved as the CSV.
- Tip: since the CSV contract has no "source" column, keep a personal notes file (e.g. `data/crops_params_sources.md`, not part of the contract) listing where each number came from — useful if someone questions a value later.
- Output: `data/crops_params.csv`.

**Zé — TE.1, then TE.2**
- What: build the site's skeleton first — map, click a field, see its harvest timeline and the 4 ranked strategy cards, plus a controls panel. Use fake data in the agreed format so you don't wait on anyone.
- How: plain HTML/CSS/JS, no framework, no build step; Leaflet.js for the map. Later (TE.2) swap the fake JSON for the real files the engine exports to `web/data/`.
- Output: a navigable page with mock data → same page reading real JSON.

Everyone: exact file formats are law — see [CONTRACTS.md](CONTRACTS.md) before writing any CSV/JSON.

**Decision (2026-11-14): GEE exports run through the Python API, not the web Code Editor.** Both Vinicius (TA.1 NDVI) and Leo (TA.3 slope) write/run `.py` scripts locally instead of pasting into code.earthengine.google.com — see `engine/gee_ndvi_export.py` as the template: it reads `data/fields.geojson` directly and saves the CSV straight to `data/`, no manual Drive download. One-time setup per machine: `pip install earthengine-api pandas`, run `earthengine authenticate` once, and have a Google Cloud project with the Earth Engine API enabled. The computation still runs on Google's servers either way — only where you write/trigger the script changes. A `.js` version of the NDVI export is kept in the repo as a fallback only, in case the API setup breaks mid-event.

## Task tracker (check off as you go)

Owners for later phases are intentionally left as **TBD** — assign when that phase starts, based on who's free.

- [x] T0.1 — Accounts and access — *everyone*
- [x] T0.2 — Repository and data contracts — done
- [x] T0.3 — Choose the demo fields — done (7 fields, see `data/fields.geojson`)
- [x] TA.1 — Export NDVI series — done
- [x] TA.2 — Download historical climate — done (Leo; `data/climate_daily.csv`, 2000→2026-11-09, no gaps)
- [x] TA.3 — Slope per field — done (Leo; `data/fields_attributes.csv`, slopes 2.5-3.7°, areas 105-129 ha)
- [x] TB.1 — Smooth the NDVI — done (Vinicius; `engine/smooth_ndvi.py`, overwrote `data/ndvi_T*.csv` in place with a daily `ndvi_smooth` column)
- [x] TB.2 — Detect emergence and peak — done (Vinicius; `engine/detect_phenology.py` → `data/phenology_T*.csv`)
- [x] TB.3 — Predict the 2025/26 harvest — done (Vinicius; `engine/predict_harvest.py` → `data/harvest_pred_T*.csv`; checkpoint PASS: P50 frozen 2025-12-15, mean |error| 6.0d, worst 9d — see model note under TB.3)
- [x] TC.1 — Parameterize candidate crops — done, reworked 2026-11-14 (Illia replaced Leo's provisional values with FAO-56-verified Kc/cycles — see `data/crop_parameter_sources.md`, which supersedes `docs/crops-params-notes.md`. Current CSV is a hybrid: Illia's values + Leo's corn window end (Feb 20), because Illia's Jan 31 lacks a verifiable SisZarc source — pending his confirmation, see the open question in `crop_parameter_sources.md`)
- [x] TC.2 — Run the historical water balance — done (Leo; `engine/water_balance.py` -> `data/success_table.csv`, sanity checks pass)
- [x] TC.3 — Bare-soil risk — done (Leo; `engine/bare_soil.py` -> `data/bare_soil_T*.csv`, ~100-110 observed bare days/yr)
- [x] TD.1 — Pest table — done (Leo; `data/pests.csv`, sources in `docs/pests-notes.md`)
- [x] TD.2 — Write the 4+ strategy cards — done (Vinicius; `web/data/strategies.json`, 4 cards with evidence from our own tables; note: `scoring.js` has its own hardcoded Portuguese labels — display name to be reconciled in review)
- [x] TD.3 — Scoring function — done (Leo; `web/js/scoring.js`, pure client-side JS)
- [x] TE.1 — Page skeleton — **Zé**
- [x] TE.2 — Connect real data — done (Leo; `engine/export_web_data.py` -> `web/data/*.json`, site fetches real data)
- [x] TE.3 — Interactivity — done (Leo; slip slider, ENSO filter, weight sliders, constraint/pest checkboxes all live)
- [x] TE.4 — All fields + polish — done (Vinicius; all 7 fields verified in web/data, 2025/26 replay highlight (mean error 6.0d), glossary tooltips, real-harvest marker on NDVI chart; still needs one manual browser pass)
- [x] TF.1 — IMEA validation — done (Vinicius; `data/imea_weekly.csv` from IMEA press coverage + `engine/imea_validation.py` → `docs/imea_validation.png`; our curve runs ~16d ahead of the state-wide series, expected since Sorriso is an early-harvest region — see `docs/imea-notes.md`)
- [x] TF.2 — Deploy — done (Vinicius; `.github/workflows/deploy-pages.yml` publishes `web/` to GitHub Pages on every push to main; Pages source set to "GitHub Actions" in repo settings)
- [x] TG.1 — Recurrent low-vigor spots per field — done (Vinicius; `engine/low_vigor_spots.py` → 7 zones in T1/T2/T4/T5, map overlay + crotalaria evidence + +8 scoring bonus)
- [x] TG.2 — "Rain left in the season" gauge (POWER climatology) — done (Vinicius; `engine/rain_odds.py` → `data/rain_odds.csv` + `web/data/rain_odds.json`, gauge follows the slip slider; odds collapse through March as expected, median rain cessation Apr 22)
- [x] TG.3 — Relative productivity per field (NDVI integral vs own history) — done (Vinicius; `engine/productivity.py` → `data/productivity_T*.csv` + `web/data/productivity.json`, panel box with 2025/26 highlighted vs the field's own mean; relative signal only, feeds TG.4)
- [ ] TG.4 — Farmer's own yield input → per-field calibration — **Vinicius**
- [ ] TG.x — **Pending HTML update pass** (`web/index.html`) — manual browser review still owed: TE.4 polish check, surface TG.1 low-vigor spots more prominently in the page (not just map tooltip), and verify the TG.2 rain gauge renders/reacts correctly — **Vinicius**
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
- **Done (2026-11-14):** ran via `engine/gee_ndvi_export.py` (Python API, see the Quick start decision above). All 7 fields exported, ~541–548 rows each, 2019→today. Checked year-by-year min/max per field: every year dips to ~0.1 and peaks ~0.9–0.95, the expected rainfed-soybean wave.

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
- **Done (2026-11-14), with a model change:** the GDD-requirement model described above was implemented first but failed the checkpoint (mean |error| 13.7d in leave-one-season-out replays — the thermal requirement implied by NDVI-detected harvests swings a lot season to season). The shipped model (`engine/predict_harvest.py`) instead predicts cycle **duration adjusted by Sep 1 → Dec 15 rainfall** (dry springs lengthen the detected cycle, r ≈ −0.7), re-centered per field, with P10/P50/P90 from the pooled residual distribution. Freeze date is **2025-12-15** (still "frozen in December"). Validation: mean |error| 6.0d, worst 9d across all 7 fields; actual harvest inside the P10–P90 window everywhere. Pitch implication: the story is "spring rainfall tells us how long the cycle will run", not growing degree-days.
- **Revisit later only if time allows (not blockers):** (1) 2025's spring rainfall (172 mm) sits *outside* the 2019–2024 range (201–420 mm), so the shipped prediction is an extrapolation — it validated fine, but flag it if a judge asks; (2) the Dec 15 freeze was picked over Dec 1 partly because Dec 1 barely missed the checkpoint (worst field 14d vs 9d) — sensitivity is mild but real; (3) P10–P90 coverage was eyeballed (7/7 actuals inside), never formally calibrated; (4) with only 42 field-seasons, richer models (GDD ensemble, 2-predictor regression) were tested and did NOT beat this — don't add complexity without new data (e.g. fields T8–T10).

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

## PHASE G — Round 3 features (added 2026-11-15, after independent state-of-the-art research)

Background: an unbiased research pass over 2024–2026 satellite-ag tools confirmed our core (NDVI harvest date → strategy ranking) matches recent literature (~5-day MAE for harvest-date detection from NDVI in MT fields, [doi:10.3390/rs17172927](https://doi.org/10.3390/rs17172927)) and found no existing tool showing a per-field window countdown + rain-duration odds. These two features extend that edge. Explicitly rejected as dishonest without ground truth: absolute yield (sacas/ha), disease *diagnosis* from imagery, field-level SMAP soil moisture, soil compaction.

### TG.1 — Recurrent low-vigor spots per field
- **Goal:** flag in-field zones whose NDVI is anomalously low **in the same place across multiple seasons** — the signature of persistent soil problems (nematode reboleiras, compaction, fertility gaps), as opposed to one-off noise (cloud, planting failure).
- **How:** GEE export of per-pixel max-NDVI composite over a ~6-week peak window (Jan±3wk, handles cloud gaps) for the last 3–5 seasons; per season, z-score each pixel against its own field's mean (removes good-year/bad-year effect); count seasons with z < −1; export zones recurring in ≥3 seasons as GeoJSON → Leaflet overlay.
- **Honest labeling (binding):** never "disease detected" — always "recurrent low-vigor zone: pattern consistent with a soil problem (nematode, compaction, fertility). Recommendation: targeted soil sampling here." Fields with recurrent zones boost crotalaria (nematode suppressor) in the strategy ranking — satellite evidence personalizes the recommendation.
- **Output:** `data/spots_<field>.geojson` + map layer + a line in the strategy-card evidence.
- **Done when:** at least one demo field shows a recurrent zone on the map with the honest label, and the crotalaria card cites it.

### TG.2 — "Rain left in the season" gauge
- **Goal:** show, per candidate sowing date, the historical odds that enough rain falls before the season ends — e.g. "sowing corn Feb 25: in ~35% of the last 25 years, rains ended before grain fill."
- **How:** pure climatology from `climate_daily.csv` (2000→2026): precompute P(≥X mm after date D) and the rainy-season cessation-date distribution; render as a simple curve/gauge next to the strategy cards. No model, no forecast.
- **Honest labeling (binding):** "historical odds", never "forecast/prediction".
- **Output:** `data/rain_odds.csv` → `web/data/rain_odds.json` + UI gauge.
- **Done when:** the gauge updates when the sowing-date slider moves and matches common sense (odds collapse through March).

### TG.3 — Relative productivity per field
- **Goal:** an honest productivity signal without ground truth: the seasonal NDVI integral (sum of daily `ndvi_smooth` between emergence and harvest) correlates with biomass/production, so each season can be compared against the field's own history.
- **How:** ~20 lines of Python over the existing `ndvi_*.csv` + `phenology_*.csv`: integral per season per field → % deviation from the field's multi-season mean. Display: "this season T3 accumulated 12% less biomass than its 4-season average."
- **Honest labeling (binding):** relative only — never convert to sacas/ha on our own (that needs calibration, which is TG.4's job).
- **Output:** `data/productivity_<field>.csv` → `web/data/productivity.json` + a line on the field panel.
- **Done when:** every demo field shows its seasonal deviation history and 2025/26 is flagged vs normal.

### TG.4 — Farmer's own yield input → per-field calibration
- **Goal:** let the farmer type in their recorded yields (sacas/ha per past season, per field) — data they often have in a notebook — and use it to calibrate TG.3's NDVI integral into an actual per-field yield estimate.
- **How:** a small form on the field panel (stored in `localStorage`, no backend — wrap reads/writes in try/catch); with ≥3 seasons entered, fit a simple linear regression yield ~ NDVI integral in client-side JS and show the 2025/26 estimate with its uncertainty; with fewer, just show their numbers alongside the relative index.
- **Why it matters for the pitch:** turns the yield limitation into a feature — "we don't invent numbers; when the data owner provides the reference, the satellite curve becomes a calibrated estimate for *their* field." Also a privacy story: the data never leaves the farmer's browser.
- **Honest labeling (binding):** show the fit quality (e.g. "based on 4 seasons you entered"); if the regression is poor, say so instead of displaying a number.
- **Output:** form + calibration logic in `web/js/` (consumes `productivity.json`; farmer data stays in `localStorage`).
- **Done when:** entering 3+ plausible yields on a demo field produces a sane estimate, and clearing them falls back to the relative view.

---

## OPTIONAL (only if everything above is done)
- **Farm-level recommendation (idea, 2026-11-14):** in practice the farmer usually plants ONE succession crop for the whole farm, not a different one per field. Besides the per-field ranking, aggregate across the 7 fields (e.g. area-weighted scores, or "best single strategy if you must pick one for everything") so the result matches how the decision is actually made. Raised by Vinicius; not yet scoped.
- **"Draw your farm" backend:** FastAPI with an `analyze_field(geojson)` endpoint that runs the same pipeline in fast mode (MODIS + POWER only), deployed on Hugging Face Spaces or Render. The demo never depends on it.
- **Literature-backed pitch polish:** cite *Agricultura Digital* (Embrapa, 2020) findings in the pitch/slides — e.g. existing Embrapa tools (ZARC Plantio Certo, SatVeg, Agritempo) as prior art we build on, and the ~4.5% climate-driven soybean yield drop (Iizumi & Ramankutty 2016) to back the water-risk axis. See [team-guide.md §9](team-guide.md#9-supporting-literature). Pure copywriting, no new pipeline — only do this after everything above is done.

## Cut order (if we fall behind)
backend → IMEA validation → El Niño filter → fewer fields. **Never cut the strategy cards.**
