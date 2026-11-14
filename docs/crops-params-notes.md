# Notes on `data/crops_params.csv` (TC.1)

Provisional parameterization — review by whoever knows agronomy best, then delete this
caveat. Values are typical literature numbers, not field-calibrated.

## Sources and reasoning

- **Kc per stage:** FAO Irrigation & Drainage Paper 56 (Allen et al., 1998) mid-season
  and initial Kc values, adapted to 4 stages (establishment / vegetative / flowering /
  grain filling). Corn mid-season Kc 1.20 is the FAO-56 reference value; sorghum and
  millet are lower (1.00 / 0.95) per FAO-56 tables; brachiaria and crotalaria use
  forage/cover-crop approximations (no grain-filling peak).
- **Cycle lengths:** typical safrinha materials in MT — corn 120 d (early hybrids),
  sorghum 110 d, millet 90 d, crotalaria ~100 d to effective cover. Brachiaria has no
  true "harvest"; 120 d covers establishment through full ground cover.
- **drought_sensitivity** ∈ [0, 1], higher = more sensitive at the critical
  (flowering) stage. Corn 0.90 (classic flowering-stage sensitivity), sorghum 0.60,
  millet 0.45 (both drought-adapted), covers 0.30–0.35 (no grain yield at stake —
  "success" means establishing cover). Semantics defined in
  `engine/water_balance.py`: tolerable mean stress at the critical stage
  = 0.10 + 0.35 x (1 − drought_sensitivity).
- **ZARC windows:** approximations of the official safrinha zoning for mid-north MT
  (corn until ~Feb 20; sorghum/millet extend into March; cover crops are not
  ZARC-regulated, window = whole quarter). Replace with exact ZARC dates per
  municipality if time allows (painelzarc.agricultura.gov.br, Sorriso-MT).
- Dates use year **2026** = the decision season (Jan–Mar 2026 sowing after the
  2025/26 soybean harvest).
