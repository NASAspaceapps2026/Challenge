# Field Shift — Team Guide

**NASA Space Apps Challenge 2026 · Challenge: "Field Shift: Adapting Farms with NASA Data" · Nov 14–15**

This document explains what we are building, why, and how — written so that anyone joining the team can understand the whole project before touching any code.

---

## 1. The problem we are solving

In Brazil's Mato Grosso grain belt, a farmer harvests soybean in Jan–Feb and then has a short rain window left before the dry season. What should go into the field next? The common answer is second-crop corn ("safrinha"), but planting it too late means drought risk, and repeating the same rotation every year degrades the soil: long bare-soil periods, erosion, and pest build-up (nematodes, corn leafhopper).

The decision depends on one key number — **when exactly will this field's soybean come off?** — and on comparing what realistically fits in the remaining window. Today farmers make this call mostly by experience, without field-specific data.

## 2. Our idea in one paragraph

For a given soybean field, we use satellite imagery to **predict the harvest date**, which tells us the real planting window left this season. Then we **compare at least four succession strategies** — the current one (second-crop corn), corn + brachiaria grass, sorghum/millet, and a cover crop (crotalaria) — scoring each on **water risk, soil protection, and pest-cycle disruption**. The result is a simple interactive web page where the farmer sees ranked "strategy cards" and can adjust them with their own priorities and constraints.

Two things to keep in mind:

- **The harvest prediction is the engine, not the product.** Its job is to measure this year's real window. The product is the strategy comparison.
- **The soil-health angle is what aligns us with the challenge.** Bare-soil days, crop residue, brachiaria and crotalaria benefits — without this, the tool is just corn logistics.

## 3. What the challenge requires (and how we match it)

The official challenge asks for a decision-support tool using NASA Earth observations plus local soil/crop information and farmer priorities. The specific requirements and our answers:

| Challenge requirement | How we meet it |
|---|---|
| Compare **≥3 rotation strategies, including the existing one** | 4 strategy cards: current corn, corn+brachiaria, sorghum/millet, cover crop |
| For each strategy: **why, evidence, benefits, information gaps, risks** | Each card follows exactly this five-part structure |
| Highlight **bare-field periods** and vulnerable seasons | Bare-soil days computed from NDVI during the dry season |
| Rotations that **interrupt pest cycles, reduce water demand, add income** | Pest table (nematodes, leafhopper) + water-balance risk + income note per card |
| Let farmers input **priorities and constraints** | Interactive controls (section 6) |
| Explain **uncertainty** and where local expertise is needed | Harvest date given as P10/P50/P90 ranges; every card carries an "ask your agronomist" notice |
| A **supportive tool, not a replacement** for farmer judgment | Explicit disclaimer in the UI and the pitch |

## 4. How it works — the pipeline

**Step 1 — Harvest prediction (the window).**
We take the field's NDVI time series (NDVI = a satellite vegetation index: high when the crop is green and growing, dropping as it matures). Sources: ESA Sentinel-2 (10 m, sharp) + NASA MODIS (daily, coarse), smoothed into one curve. The curve gives us emergence and peak dates; combined with the field's own history and accumulated growing degree-days, we project the harvest date as **P10 / P50 / P90** (optimistic / expected / pessimistic).

**Step 2 — Climate risk (what fits in the window).**
Using 25+ years of NASA POWER (temperature, radiation) and GPM/IMERG (rainfall), we run a simple crop water balance for each candidate crop and each possible sowing date. Output: a table of **"probability of success" per crop per sowing date**, with an El Niño / La Niña / neutral filter and frost risk.

**Step 3 — Soil and pests.**
From NDVI we count **bare-soil days** in the dry season (a key soil-degradation indicator). From SRTM elevation data we derive **slope → erosion risk** per field. A simple lookup table (Embrapa/ZARC sources) maps crops to pest effects — e.g., crotalaria suppresses nematodes.

**Step 4 — Scoring and cards.**
Each strategy gets a score combining income potential × soil protection × risk, weighted by the farmer's stated priorities. The top of the page shows the harvest window; below it, the ranked strategy cards.

**Step 5 — Validation (no field data needed).**
We compare our predicted regional "% harvested" curve against IMEA's published weekly harvest-progress series for Mato Grosso. If the curves match, the engine is credible.

## 5. Scope — deliberately narrow

- **Crop:** soybean summer crop only. No sugarcane, no irrigation.
- **Region:** mid-north Mato Grosso (Sorriso / Lucas do Rio Verde). Western Bahia is the fallback.
- **Demo:** a "demonstration farm" of 5–10 neighboring fields (no owner identified), pre-computed. Fields chosen for variety: early vs. late planting, with and without second crop.
- **Harvest demo = replay of the 2025/26 season:** "what the model said in December vs. when the field was actually harvested." (During the event, the current soybean crop is still ~30–60 days from harvest, so a replay is the honest demo.)

## 6. What the farmer can adjust (interactivity)

Everything runs **in the browser over pre-computed tables** — no server needed, so the demo can never break.

| Farmer input | Effect |
|---|---|
| Soybean planting date & cultivar cycle (early/mid/late) | Refines the predicted harvest date |
| Slider: "what if harvest slips X days?" | Strategy ranking updates instantly |
| Climate scenario (auto from forecast, or manual) | Swaps the risk table |
| Constraints: has cattle? corn contract? specific machinery? | Enables/disables strategies (e.g., cattle favors brachiaria) |
| Known pests (nematode, leafhopper) | Bonus to crotalaria, brachiaria, sorghum |
| Priority weights: income × soil protection × lower risk | Changes the final score |

An **optional backend** ("draw any farm on a map" → FastAPI calls the same analysis function live) is a stretch goal, built only after everything above works.

## 7. Data sources at a glance

| Source | Agency | What we use it for |
|---|---|---|
| MODIS + Sentinel-2 | NASA + ESA | NDVI series → harvest prediction, bare-soil days |
| NASA POWER | NASA | 25+ yr daily temperature/radiation → degree-days, water balance |
| GPM / IMERG | NASA | 25+ yr rainfall → water balance, extreme-rain risk |
| SRTM | NASA | Slope → erosion risk per field |
| IMEA | Local (MT) | Weekly harvest-progress series → validation |
| Embrapa / ZARC | Local (BR) | Crop characteristics, sowing windows, pest table |

## 8. Two-day plan

**Day 1 — the engine.**
Kickoff and scope freeze → fire Google Earth Engine exports early (they take hours) → harvest prediction and water balance built in parallel → **checkpoint: one field working end-to-end in the browser.** Sleep.

**Day 2 — the product.**
Strategy cards, scoring and farmer controls → all demo fields → deploy to GitHub Pages → backend only if time allows → **feature freeze 8h before the deadline** → video, slides, project page → **submit 1h before the deadline.**

**If we fall behind, cut in this order:** backend → IMEA validation → El Niño filter → fewer fields. **Never cut the strategy cards with the soil-health content — they are the challenge.**

## 9. Supporting literature

Notes from *Agricultura Digital* (Embrapa, 2020) relevant to our approach:

- **Prior art to position against:** Embrapa already has short-term decision tools — WebAgritec, Zarc Plantio Certo, SatVeg, Agritempo — and a medium/long-term simulator, ScenAgri, still under development. Useful to cite in the pitch as "existing tools do X; we add the succession-strategy comparison on top."
- **NDVI alone isn't enough:** different stress types (water, pest, disease) can produce similar NDVI signals; the trend in the literature is to combine imagery with weather, management history, and soil data. We already do this (water balance + pest table + slope), but it's worth stating explicitly in the pitch as a known limitation we've addressed.
- **Quantified climate risk on soybean:** Iizumi & Ramankutty (2016), cited in the book, attribute to climate change an average soybean yield drop of ~4.5% globally over 1981–2010 (vs. ~4.1% maize, ~1.8% wheat). Usable as a citation backing the "water risk" axis.
- **Disease-risk signal:** rainfall/humidity/leaf-wetness data can estimate disease incidence probability — supports the pest/disease-cycle axis of our scoring, beyond just nematodes/leafhopper.
- Nothing in the book gave concrete corn/brachiaria/sorghum/crotalaria rotation parameters or water-balance formulas we could plug in directly — our scoring logic still needs to come from Embrapa/ZARC agronomic references as already planned.

## 10. Glossary

- **NDVI** — Normalized Difference Vegetation Index; satellite measure of green vegetation (0 = bare soil, ~0.9 = dense healthy crop).
- **Safrinha** — Brazil's second crop, planted right after soybean harvest in the same season.
- **Water balance** — day-by-day accounting of rainfall in vs. crop water demand out; tells whether a crop would run out of water.
- **Degree-days** — accumulated heat over time; crops need a fixed amount to mature, so it predicts development speed.
- **P10/P50/P90** — the 10th/50th/90th percentile of our prediction: "there's a 10% chance harvest comes before P10, 50% before P50…"
- **Brachiaria / crotalaria** — forage grass and legume cover crop; both protect soil, and crotalaria suppresses nematodes.
- **GEE** — Google Earth Engine, the platform we use to pull and process satellite data.
- **IMEA** — Mato Grosso's agricultural economics institute; publishes weekly harvest progress.
- **ZARC** — Brazil's official agricultural climate-risk zoning (sowing windows per crop/region).
