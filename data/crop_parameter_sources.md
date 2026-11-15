# Data Sources and Parameter Justification (crops_params.md)

**Context:** Data adapted for modeling the second crop (Safrinha) and cover crops in the state of Mato Grosso (municipalities of Sorriso / Lucas do Rio Verde).

## 1. cycle_days (Cycle Length)
*   **Sources:** ZARC (maturity group classification - Grupo I, II, III), Fundação MT technical bulletins, and seed originator catalogs (Embrapa, Pioneer, Dekalb) for the Cerrado region.
*   **Justification:** Reflects typical periods from sowing to physiological maturity/cutting under tropical climate conditions (where the cycle in days is shorter due to high temperatures). 
    *   *Corn (130)*: Medium maturity hybrids (Grupo II/III), typical for safrinha.
    *   *Sorghum (115)*: Grain sorghum, slightly faster cycle than corn.
    *   *Millet (90)*: Grown as a fast cover crop (Milheto).
    *   *Brachiaria (120)*: Cycle until desiccation before sowing the next commercial crop.
    *   *Crotalaria (100)*: Cycle until cutting (flowering) of the leguminous green manure.

## 2. kc_establishment / kc_vegetative / kc_flowering / kc_filling (Crop Coefficients)
*   **Source:** FAO Irrigation & Drainage Paper 56 (Allen et al. 1998). Specifically, **Table 12** (Single crop coefficient, $K_c$).
*   **Justification:** The single crop coefficient ($K_c$) approach was used, which integrates both plant transpiration and time-averaged soil surface evaporation. The base value for the initial stage of cereals is taken as 0.3. 
    *   *Corn, Sorghum, Millet*: Base values taken directly from FAO-56.
    *   *Brachiaria, Crotalaria*: No exact matches under these names exist in FAO-56. Values were approximated based on FAO data for grazing pasture and leguminous crops (legumes/cowpeas), and adjusted considering Embrapa Agrobiologia recommendations for tropical cover crops.

## 3. drought_sensitivity
*   **Sources:** Agronomic consensus, Embrapa Milho e Sorgo publications on crop tolerance to water stress.
*   **Justification:** A relative linear scale from 0.0 (maximum tolerance) to 1.0 (maximum vulnerability) was created. 
    *   *Corn (0.8)*: The most vulnerable crop, especially during the silking (flowering) phase. A halt in rainfall is fatal for the yield.
    *   *Sorghum (0.4)*: Known for its ability to enter semi-dormancy during droughts and recover.
    *   *Millet (0.2)*: Historically the most drought-tolerant crop on the list.
    *   *Sanity check*: Corn (0.8) > Sorghum (0.4) > Millet (0.2) is maintained.

## 4. zarc_window_start / zarc_window_end (Sowing Windows)
*   **Source:** Official ZARC portal (Zoneamento Agrícola de Risco Climático) by MAPA (Ministério da Agricultura e Pecuária).
*   **Query Parameters:** Safra 2026/2027, MT, Sorriso (or Lucas do Rio Verde), Solo Tipo 2/3.
*   **Justification:** The window is formed from 10-day periods (decêndios) where the climatic risk of crop loss is 20% or 30% (green and yellow zones).
    *   The end of the window for corn (February 28) reflects a strict limit — after this date, the risk exceeds 40% due to the end of the rainy season.
    *   Cover crops and sorghum are less demanding for moisture, so their ZARC windows are officially extended to mid-to-late March.
