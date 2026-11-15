/* TD.3 — strategy scoring, plain JS, runs fully in the browser.
 *
 * score = w1*income + w2*soil_protection + w3*(1 - risk), normalized 0-100
 * (docs/CONTRACTS.md). Pure functions over the pre-computed tables in
 * web/data/ — no network, no server.
 *
 * Strategy ids are canonical (docs/CONTRACTS.md):
 *   current_corn, corn_brachiaria, sorghum_millet, cover_crotalaria
 */

const STRATEGIES = {
  current_corn:     { crop: "corn",       income: 90, label: "Second-crop corn (current)" },
  corn_brachiaria:  { crop: "corn",       income: 85, label: "Corn + brachiaria" },
  sorghum_millet:   { crop: "sorghum",    income: 55, label: "Sorghum / millet" },
  cover_crotalaria: { crop: "crotalaria", income: 15, label: "Cover crop (crotalaria)" },
};

const DRY_SEASON_DAYS = 153; // May 1 .. Sep 30

/* Probability of success for a crop sown on `sowingISO` (YYYY-MM-DD, year 2026
 * grid) under `scenario`, from the nested success_table.json. Snaps to the
 * nearest 5-day grid date; clamps outside the grid. */
function successProb(successTable, crop, scenario, sowingISO) {
  const table = successTable[crop] && successTable[crop][scenario];
  if (!table) return null;
  const dates = Object.keys(table).sort();
  if (sowingISO <= dates[0]) return table[dates[0]];
  const last = dates[dates.length - 1];
  if (sowingISO >= last) return table[last];
  let best = dates[0];
  for (const d of dates) {
    if (Math.abs(Date.parse(d) - Date.parse(sowingISO)) <
        Math.abs(Date.parse(best) - Date.parse(sowingISO))) best = d;
  }
  return table[best];
}

/* Sum of pest effects (-2..+2 each) for a crop, restricted to the pests the
 * farmer flagged; empty selection means no pest signal. */
function pestEffect(pests, crop, selectedPests) {
  let sum = 0;
  for (const row of pests) {
    if (row.crop === crop && selectedPests.includes(row.pest)) {
      sum += Number(row.effect);
    }
  }
  return sum; // realistic range with 3 pests: -5 .. +4
}

/* Soil protection 0..1: dry-season cover (dominant), pest-cycle effect,
 * and erosion exposure from slope. */
function soilProtection({ bareDays, pestSum, slopeDeg }) {
  const cover = 1 - Math.min(1, bareDays / DRY_SEASON_DAYS);
  const pest = (Math.max(-5, Math.min(5, pestSum)) + 5) / 10;
  const erosion = 1 - Math.min(1, (slopeDeg || 0) / 5); // 5 deg = full flag
  return 0.6 * cover + 0.3 * pest + 0.1 * erosion;
}

/* Score every strategy for one field.
 *
 * inputs = {
 *   sowingISO:  "YYYY-MM-DD"  planned sowing (harvest p50 + slip + turnaround)
 *   scenario:   "all" | "nino" | "nina" | "neutral"
 *   weights:    { income, soil, risk }      each 0..1 (slider values)
 *   selectedPests: ["nematode", ...]        farmer-flagged pests
 *   constraints: { cattle, cornContract }   booleans
 *   slopeDeg:   field slope
 *   bareSoil:   { strategyId: meanBareDays }  from bare_soil.json
 *   successTable, pests: parsed JSON tables
 * }
 * Returns [{id, label, score, risk, incomeN, protection, disabled, reason}]
 * sorted best-first (disabled strategies sink to the bottom).
 */
function scoreStrategies(inputs) {
  const { weights } = inputs;
  const wSum = weights.income + weights.soil + weights.risk || 1;
  const out = [];
  for (const [id, s] of Object.entries(STRATEGIES)) {
    const prob = successProb(
      inputs.successTable, s.crop, inputs.scenario, inputs.sowingISO);
    const risk = prob === null ? 0.5 : 1 - prob;
    const pestSum = pestEffect(inputs.pests, s.crop, inputs.selectedPests || []);
    const protection = soilProtection({
      bareDays: (inputs.bareSoil && inputs.bareSoil[id]) ?? DRY_SEASON_DAYS,
      pestSum,
      slopeDeg: inputs.slopeDeg,
    });

    let disabled = false, reason = "";
    const c = inputs.constraints || {};
    if (c.cornContract && s.crop !== "corn") {
      disabled = true; reason = "A corn contract requires planting corn";
    }

    let bonus = 0;
    if (c.cattle && id === "corn_brachiaria") bonus = 5; // pasture value
    // TG.1 — field has recurrent low-vigor zones (pattern consistent with a
    // soil problem, e.g. nematodes): crotalaria is a nematode suppressor.
    if (inputs.recurrentSpots && id === "cover_crotalaria") bonus += 8;

    const score01 =
      (weights.income * (s.income / 100) +
       weights.soil * protection +
       weights.risk * (1 - risk)) / wSum;

    out.push({
      id, label: s.label, crop: s.crop,
      score: Math.round(Math.max(0, Math.min(100, score01 * 100 + bonus))),
      risk, successProb: prob, protection, incomeN: s.income,
      pestSum, disabled, reason,
    });
  }
  out.sort((a, b) => (a.disabled - b.disabled) || (b.score - a.score));
  return out;
}

/* Expose for the page (no module system — plain <script> include). */
window.FieldShiftScoring = { STRATEGIES, scoreStrategies, successProb };
