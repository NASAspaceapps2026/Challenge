# Notes on `data/pests.csv` (TD.1)

Scale: `effect` ∈ [−2, +2]. Negative = growing this crop in succession favors the
pest (host / multiplies it); positive = suppresses it or breaks its cycle.
Qualitative, from Embrapa technical literature — good enough for a relative score,
not a prescription (the agronomist disclaimer covers this).

## nematode (root-lesion *Pratylenchus brachyurus*, the key soybean nematode in MT)

- **crotalaria +2** — *Crotalaria spectabilis/ochroleuca* is the classic antagonist
  cover crop: nematodes penetrate roots but cannot reproduce (trap crop). Embrapa
  Soja recommends it specifically for *P. brachyurus* management.
- **brachiaria +1** — *Urochloa ruziziensis* reduces population densities relative
  to corn in most Embrapa trials (poor host), though not as strongly as crotalaria.
- **millet +1** — depends on cultivar (ADR 300 reduces; common cultivars can host),
  scored +1 with the cultivar caveat in the strategy card.
- **corn −1 / sorghum −1** — both maintain or multiply *P. brachyurus* populations
  (hosts), keeping pressure on the next soybean crop.

## corn_leafhopper (*Dalbulus maidis*, vector of corn stunt / "enfezamento")

- **corn −2** — safrinha corn right after soybean is the "green bridge" that keeps
  the vector and the stunt pathogens alive year-round; the main driver of the
  current MT outbreak.
- **all non-corn crops +1** — *D. maidis* only reproduces on corn (Zea), so any
  corn-free season breaks the green bridge regionally.

## fall_armyworm (*Spodoptera frugiperda*)

- **corn −2** — primary host; safrinha corn sustains populations and resistance
  pressure on Bt traits.
- **sorghum/millet/brachiaria −1** — alternative grass hosts (lesser but real).
- **crotalaria +1** — non-grass legume, interrupts the grass-host sequence.

Review by an agronomy-minded teammate welcome; if any value changes, re-run only
TD.3 (scores) — nothing upstream depends on this table.
