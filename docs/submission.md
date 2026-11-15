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

*(200 words, per the platform's recommendation)*

Soybean farmers in Mato Grosso, Brazil, decide every February what to plant after
harvest. The rain window is short, and the choice determines water risk, soil
health and pest pressure for the following years. This decision is currently made
by experience, without data specific to each field.

Field Shift supports that decision with satellite data. The tool reads each
field's NDVI history from NASA MODIS and ESA Sentinel-2 and predicts the soybean
harvest date as a P10, P50 and P90 range. This range measures the planting window
remaining in the season. The tool then evaluates four succession
strategies: second-crop corn, the current practice, corn with brachiaria,
sorghum or millet, and a crotalaria cover crop. Each strategy is tested against
26 years of NASA POWER and GPM rainfall in a daily water balance, scored on
bare-soil days observed by satellite, and adjusted for slope from SRTM and for
pest cycle effects. The farmer sets the weight given to income, soil protection
and risk.

The interface is a satellite map of seven demonstration fields near Sorriso, with
ranked strategy cards per field. It runs entirely in the browser, works on a
phone, and states explicitly where the data ends and the agronomist's judgment
begins.

## Project Demo

*(link to the 30-second video — script at the bottom of this file)*

## Project Link

https://nasaspaceapps2026.github.io/Challenge/

## Detailed Description

The farmer selects a field on a satellite map. The page shows the predicted
harvest window (P10, P50, P90), the field's NDVI curve with that window marked,
and four ranked strategy cards for what to plant after the soybean. The controls
re-rank the cards instantly: a slider for harvest delay, an El Niño and La Niña
filter, priority weights for income, soil protection and risk, and checkboxes for
constraints such as owning cattle, holding a corn contract, or known pest
presence.

The pipeline has four stages. All code is open source in the repository.

1. Harvest prediction. For each field, Sentinel-2 (10 m) and MODIS (daily) NDVI
   from 2019 onward are merged, smoothed with a Savitzky-Golay filter, and used
   to detect emergence, peak and harvest dates for every past season. The
   distribution of the field's own emergence-to-harvest durations, adjusted by
   growing degree-days computed from NASA POWER temperatures, produces the P10,
   P50 and P90 harvest dates for the current season. In a replay of the 2025/26
   season with data frozen in December, the P50 prediction fell within 10 days
   of the harvest date later detected by satellite.

2. Climate risk. For each candidate crop, each sowing date from January to March
   on a 5-day grid, and each year from 2000 to 2025, the tool simulates a daily
   100 mm soil water balance: NASA POWER and GPM rainfall in, crop demand out,
   with reference evapotranspiration derived from radiation and FAO-56 stage
   coefficients. A year counts as a failure when water stress during the crop's
   flowering stage exceeds its tolerance. The share of successful years is the
   success probability, also computed separately for El Niño, La Niña and
   neutral years classified by the NOAA ONI index. The results match agronomic
   experience: corn sown on February 1 succeeds in 77% of historical years,
   close to 0% by March, while millet still succeeds in about 70% of years in
   mid-March.

3. Soil and pests. Bare-soil days are dry-season days with smoothed NDVI below
   0.30. The fields show 100 to 110 bare days per year under the current
   rotation. Slope from SRTM provides the erosion component. A table built from
   Embrapa sources maps each crop's effect on nematodes, corn leafhopper and
   fall armyworm; crotalaria suppresses nematodes, and second-crop corn
   sustains the leafhopper population between seasons.

4. Scoring. Each strategy receives a score combining income potential, soil
   protection and success probability, normalized to a 0-100 scale and weighted
   by the farmer's slider settings. The computation runs client-side in plain
   JavaScript.

Python scripts produce small CSV and JSON tables committed to the repository.
The site is static HTML, CSS and JavaScript hosted on GitHub Pages and fetches
those tables directly. There is no server.

Predictions are presented as ranges, each card lists its information gaps, and a
fixed notice states that the tool supports the farmer's agronomist and does not
replace them.

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
