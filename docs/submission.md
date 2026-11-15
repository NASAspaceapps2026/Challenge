# TF.3 — Submission kit

Copy-paste material for the Space Apps project page. The platform fields map to the
sections below. Fill the project page early, submit **at least 1 hour before the
deadline** (plan rule). The team Owner edits the page: profile → My Teams → team →
Create/Edit Project.

Live site: https://nasaspaceapps2026.github.io/Challenge/ *(confirm the exact Pages
URL in repo Settings → Pages before pasting)*
Repo: https://github.com/NASAspaceapps2026/Challenge

---

## Project name

**Field Shift — When will the soybean come off, and what should follow it?**

## High-Level Summary

In Brazil's Mato Grosso grain belt, every soybean farmer faces the same February
question: the crop is about to come off, a short rain window remains, and whatever
is planted next — or nothing — will shape the farm's water risk, soil health and
pest pressure for years. Today that call is made by experience, without
field-specific data.

Field Shift answers it with satellites. From each field's own NDVI history
(NASA MODIS + ESA Sentinel-2) we predict the soybean harvest date as an uncertainty
range (P10/P50/P90), which measures the *real* planting window left this season.
We then rank four succession strategies — second-crop corn (the current practice),
corn + brachiaria grass, sorghum/millet, and a crotalaria cover crop — by running
each one through 26 years of NASA POWER and GPM rainfall in a daily crop water
balance, counting satellite-observed bare-soil days, factoring slope-driven erosion
risk (SRTM) and pest-cycle effects, and weighting everything by the farmer's own
priorities: income, soil protection, lower risk.

The result is a simple interactive web page — ranked strategy cards over a
clickable satellite map of a 7-field demonstration farm near Sorriso (MT). Our
dry-season data shows these fields bare for ~100–110 of 153 dry-season days under
the current rotation: the tool makes the cost of that visible, and shows what
realistically fits in each field's window. It runs entirely in the browser on
pre-computed tables, works on a phone, and explicitly tells the farmer where the
data ends and their agronomist begins.

## Project Demo

*(link to the 30-second video — script at the bottom of this file)*

## Project Link

https://nasaspaceapps2026.github.io/Challenge/

## Detailed Description

**What it does.** The farmer picks a field on a satellite map. The page shows the
predicted harvest window (P10/P50/P90), the field's NDVI life-curve with that
window drawn on it, and four ranked strategy cards for what to plant after the
soybean. Sliders and checkboxes ("what if harvest slips 10 days?", El Niño/La Niña
filter, income vs. soil vs. risk priorities, "I have cattle", "corn contract",
known pests) re-rank the cards instantly.

**How it works — pipeline (all open source in the repo):**

1. *Harvest prediction.* Per field, we fuse Sentinel-2 (10 m) and MODIS (daily)
   NDVI from 2019 on, smooth with a Savitzky–Golay filter, and detect emergence,
   peak and harvest dates for every past season. The field's own
   emergence→harvest duration distribution, adjusted by growing degree-days from
   NASA POWER temperatures, yields P10/P50/P90 harvest dates for the current
   season. Our December-frozen replay of the 2025/26 season passed the ≤10-day
   checkpoint against the satellite-detected harvest.
2. *What fits in the window.* For each candidate crop × sowing date (Jan–Mar,
   5-day grid) × each year 2000–2025, we simulate a daily 100 mm soil-water
   bucket: NASA POWER + GPM rainfall in, crop demand out (radiation-based ET0 ×
   FAO-56 stage coefficients). A year fails if water stress at the crop's
   critical (flowering) stage exceeds its tolerance. The share of non-failing
   years is the success probability — also split by El Niño/La Niña/neutral
   (NOAA ONI). The table reproduces agronomic common sense: corn sown Feb 1 ≈
   77% success, collapsing to ~0% by March, while millet still holds ~70% in
   mid-March.
3. *Soil and pests.* Bare-soil days = dry-season days with smoothed NDVI < 0.30
   (observed ~100–110 days/yr under the current rotation). Slope per field from
   SRTM gives erosion exposure. An Embrapa-sourced table maps each crop's effect
   on nematodes, corn leafhopper and fall armyworm (e.g., crotalaria suppresses
   nematodes; corn safrinha is the leafhopper's green bridge).
4. *Scoring.* score = w₁·income + w₂·soil_protection + w₃·(1−risk), normalized
   0–100, computed client-side in plain JS. The weights are the farmer's sliders.

**Architecture.** Python scripts produce small CSV/JSON tables committed to the
repo; the site is static HTML/CSS/JS on GitHub Pages fetching those tables — no
server, nothing to break during a demo.

**Honesty by design.** Predictions are shown as ranges, every card lists
"what we don't know", and a fixed notice says the tool supports — never replaces —
the farmer's agronomist.

## NASA Data

- **MODIS (MOD09GQ/MOD13, Terra/Aqua)** — daily NDVI to gap-fill cloudy Sentinel-2
  periods; basis of the harvest-date engine. https://modis.gsfc.nasa.gov/
- **NASA POWER** — 26 years of daily Tmin/Tmax/radiation at the farm: degree-days
  and ET0 for the water balance. https://power.larc.nasa.gov/
- **GPM / IMERG** — daily rainfall driving the historical water balance.
  https://gpm.nasa.gov/
- **SRTM (SRTMGL1)** — slope per field → erosion component of the soil score.
  https://www.earthdata.nasa.gov/data/instruments/srtm

**Partner & other data:** ESA Copernicus Sentinel-2 (10 m NDVI); NOAA ONI
(El Niño classification); Embrapa / FAO-56 / ZARC (crop parameters, pest effects,
sowing windows); IMEA (weekly harvest progress used to validate the regional
prediction curve).

## Use of Artificial Intelligence

We used Anthropic's Claude (via Claude Code) as a programming assistant to write
and review code and draft documentation. All agronomic parameters come from the
cited public sources (FAO-56, Embrapa, ZARC, NOAA), all satellite/climate
processing is our own open code in the repo, and every number shown in the tool is
reproducible by running the scripts. No generative AI imagery; satellite imagery
basemap © Esri.

## References

- Allen, R. et al. (1998). *FAO Irrigation & Drainage Paper 56* — crop
  coefficients and ET0.
- Embrapa technical literature on safrinha systems, *Pratylenchus brachyurus*
  management (crotalaria/brachiaria) and corn leafhopper ("enfezamento").
- ZARC — Zoneamento Agrícola de Risco Climático (MAPA): official sowing windows.
- NOAA Climate Prediction Center — ONI index (ENSO year classification).
- IMEA — weekly soybean harvest progress, Mato Grosso.
- Full source list per table: `docs/crops-params-notes.md`, `docs/pests-notes.md`.

---

## 30-second demo video — script

Screen recording of the live site (phone or desktop), voice-over or captions.
Record in English if comfortable; English captions otherwise.

| t | Screen | Line (VO/caption) |
|---|---|---|
| 0–4s | Satellite map, 7 fields | "After soybean, Mato Grosso farmers have one short rain window. What fits in it?" |
| 4–9s | Click field T5 | "Field Shift reads each field's own satellite history…" |
| 9–14s | Harvest window P10/P50/P90 + NDVI curve | "…and predicts when the soybean comes off — with honest uncertainty." |
| 14–21s | Ranked strategy cards | "Then it ranks four succession strategies using 26 years of NASA rainfall: water risk, bare-soil days, pest cycles." |
| 21–26s | Drag the slip slider; ranking reshuffles | "If harvest slips ten days — corn falls, millet rises. Instantly." |
| 26–30s | Disclaimer + logo/title card | "Built on NASA data. Decided with your agronomist. Field Shift." |

Tips: 1080p, hide bookmarks bar, pre-select La Niña OFF/defaults, rehearse the
slider move once so the reshuffle is visible. Upload to YouTube (unlisted is fine)
and paste the link in Project Demo.
