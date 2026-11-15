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
ranked strategy cards per field. It runs in the browser, works on a phone, and
states where the data ends and the agronomist's judgment begins.

## Project Demo

*(link to the 30-second video — script at the bottom of this file)*

## Project Link

https://nasaspaceapps2026.github.io/Challenge/

## Detailed Description

Brazil harvests the largest soybean crop on Earth, about 180 million tonnes in
2025/26, and the state of Mato Grosso alone produces more than 50 million of
them, more than any country except the United States, Argentina and Brazil
itself. Almost all of it is rainfed. When the soybean comes off in January and
February, the same land immediately hosts Brazil's second-crop corn, the
"safrinha", and Mato Grosso again leads with 49% of the national safrinha
production. This double-crop system feeds a large share of the world's grain
trade, and it hangs on one narrow hinge: the few weeks of rain left between the
soybean harvest and the dry season.

Every February, each farmer decides what goes into that window. Sow corn too
late and it flowers into drought; repeat corn year after year and the soil
spends the dry season bare while nematodes and the corn leafhopper build up.
The information needed to decide well exists, but it is scattered: satellites
observe every field, decades of rainfall are public, and the agronomic
literature is clear about rotation benefits. What is missing is a tool that
brings all of it down to the scale where the decision is actually made, the
individual field. That is what Field Shift does.

The farmer selects a field on a satellite map. The page shows the predicted
harvest window as three dates, P10, P50 and P90: there is a 10% chance the
harvest happens before the P10 date, 50% before P50, and 90% before P90. P50 is
the expected date, and the interval from P10 to P90 expresses how certain the
prediction is. The page also shows the field's NDVI curve with that window
marked, and four ranked strategy cards for what to plant after the soybean:
second-crop corn, which is the current practice, corn with brachiaria, sorghum
or millet, and a crotalaria cover crop. The controls re-rank the cards
instantly: a slider for harvest delay, an El Nino and La Nina filter, priority
weights for income, soil protection and risk, and checkboxes for constraints
such as owning cattle, holding a corn contract, or known pest presence.

The pipeline has four stages, each grounded in published literature, and all
code is open source in the repository. The first stage predicts the harvest.
Detecting crop stages from smoothed vegetation-index time series is an
established method, with reported errors of 3 to 12 days for rice, maize and
soybean (Sakamoto et al., 2005, Remote Sensing of Environment 96:366-374;
Sakamoto et al., 2010, RSE 114:2146-2159). For each field, Sentinel-2 (10 m)
and MODIS (daily) NDVI from 2019 onward are merged and smoothed with a
Savitzky-Golay filter, the standard method for reconstructing NDVI series under
cloud contamination (Chen et al., 2004, RSE 91:332-344), and used to detect
emergence, peak and harvest dates for every past season. The distribution of
the field's own emergence-to-harvest durations, adjusted by growing degree-days
computed from NASA POWER temperatures, produces the P10, P50 and P90 dates for
the current season. In a replay of the 2025/26 season with data frozen in
December, the P50 prediction fell within 10 days of the harvest date later
detected by satellite.

The second stage measures climate risk. For each candidate crop, each sowing
date from January to March on a 5-day grid, and each year from 2000 to 2025,
the tool simulates a daily 100 mm soil water balance: NASA POWER and GPM
rainfall in, crop demand out, with reference evapotranspiration derived from
radiation and stage coefficients from the FAO Irrigation and Drainage Paper 56
(Allen et al., 1998). This is the same logic Brazil's official climate-risk
zoning (ZARC/MAPA) uses to define sowing windows from simulated water balance.
A year counts as a failure when water stress during the crop's flowering stage
exceeds its tolerance, and the share of successful years is the success
probability. The results reproduce the gradient documented in Embrapa's
second-crop corn literature, where yield potential falls and drought risk rises
as sowing is delayed: in our table, corn sown on February 1 succeeds in 77% of
historical years and close to 0% by March, while millet still succeeds in about
70% of years in mid-March. The probability is also computed separately for El
Nino, La Nina and neutral years classified by the NOAA ONI index, following
evidence that ENSO phase changes the length and timing of the sowing window in
Central Brazil and that cropping calendars should be adjusted per phase
(Heinemann et al., 2021, International Journal of Climatology,
doi 10.1002/joc.6684).

The third stage covers soil and pests. Bare-soil days are dry-season days with
smoothed NDVI below 0.30; the demonstration fields show 100 to 110 bare days
per year under the current rotation. Field studies in Brazil justify this as a
degradation indicator: soil and water losses fall sharply with residue cover,
with roughly half the runoff at 90% cover compared to bare soil (Bragantia,
2015). Slope from SRTM provides the erosion component. The pest table is built
from the regional literature. Off-season Crotalaria spectabilis, alone or with
ADR 300 pearl millet, was the most suitable option to reduce Pratylenchus
brachyurus populations and soybean damage in trials run in Vera, Mato Grosso,
the same region as our demonstration farm (Debiasi et al., 2016, Pesquisa
Agropecuaria Brasileira), with suppression confirmed for sole-cropped
crotalaria species (Cruz et al., 2020, Ciencia Rural). For the corn leafhopper,
the corn-stunt outbreak in Brazil is attributed to overlapping corn seasons
that sustain Dalbulus maidis year-round, with annual losses estimated at
US$6.5 billion, and breaking that green bridge is listed among the core
management measures (Pozebon et al., 2022, Journal of Economic Entomology,
doi 10.1093/jee/toac147). Our score therefore penalizes corn after corn and
rewards a corn-free season when these pests are flagged. The corn-brachiaria
card follows Embrapa trials showing the consortium maintains second-crop corn
yield while adding straw, with following-season soybean outyielding soybean
grown over sole-corn residue by about 7 sacks per hectare.

The fourth stage is the score: each strategy combines income potential, soil
protection and success probability, normalized to a 0-100 scale and weighted by
the farmer's slider settings, computed client-side in plain JavaScript.

The immediate benefit is a better-timed succession decision: the tool shows
each field's real planting window and the historical odds of each option, so
the farmer can avoid sowing corn into a window where it fails in most years, or
discover that a cover crop fits where a cash crop does not. At Mato Grosso's
scale, where millions of hectares make this same call in the same few weeks,
even marginal improvements in sowing timing and rotation choice move national
production and reduce losses like the US$6.5 billion a year already attributed
to the corn leafhopper alone. The longer-term impact is on the soil that
sustains the system, and the method generalizes: every input is a public
satellite or climate product, so the same pipeline can be run for any rainfed
grain region in the world.

The project was developed with Google Earth Engine (JavaScript and Python) for
satellite exports, Python with pandas and SciPy for NDVI smoothing, phenology
detection, the water balance and the scoring tables, and plain HTML, CSS and
JavaScript with Leaflet and Tailwind for the site. The site is static, hosted
on GitHub Pages, and reads pre-computed JSON tables. There is no server and no
build step, so the demo cannot fail from infrastructure.

The creative core of the project is that the harvest prediction is not the
product but the measuring instrument. Most crop tools predict yield; Field
Shift predicts a date, because the date is what converts satellite data into an
agronomic decision: how many days of rain remain. A second deliberate choice is
honesty as a design feature. Predictions appear as P10, P50 and P90 ranges
rather than single dates, every strategy card lists what the data does not
cover, and a fixed notice states that the tool supports the farmer's agronomist
and does not replace them.

The team considered three main factors. Scope was cut deliberately to one crop
system, one region and seven real fields, so that every number shown could be
computed and verified within the event. Results were validated instead of
assumed: the harvest model was tested by replaying the 2025/26 season with data
frozen in December, and the water balance was accepted only after it reproduced
the behavior documented in the agronomic literature cited above. Finally, the
user shaped the interface: it is in Portuguese, built for a farmer on a phone,
and avoids technical vocabulary except where a tooltip can explain it.

Regarding the use of artificial intelligence: the team used Anthropic's Claude
as an assistant for coding and for drafting text, always under team direction
and review. Parts of the Python pipeline, the JavaScript scoring code and the
site were written or reviewed with Claude, recorded in every repository
commit's metadata, and the documentation and the text on this page were drafted
with Claude and edited by the team. No AI-generated images, video or audio were
used, and the tool itself contains no AI component: it is a deterministic
pipeline whose every number is reproducible from the open scripts and cited
public sources.

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

**Where to put this:** the platform's SI checkboxes are data-collection only and
hidden from judges. Judges only see what is inside the project page itself, so
paste the paragraph below as the FINAL paragraph of Project Details (after
"...except where a tooltip can explain it."). Keep it here too in case the form
offers a dedicated visible AI field.

We used Anthropic's Claude (via Claude Code) in two ways, both under team
direction and review. First, as a programming assistant: parts of the Python
pipeline, the JavaScript scoring code and the site were written or reviewed with
Claude, and the repository records this in every commit's metadata
(Co-Authored-By trailer). Second, as a writing assistant: the project
documentation and the text on this project page were drafted with Claude and
edited by the team.

No AI-generated images, video or audio were used; the satellite basemap is
(c) Esri. The tool itself contains no AI or machine-learning component: it is a
deterministic pipeline. All agronomic parameters come from the cited public
sources (FAO-56, Embrapa, ZARC, NOAA), and every number shown in the tool is
reproducible by running the open scripts in the repository.

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
