# IMEA weekly harvest data — sources (TF.1)

`data/imea_weekly.csv` holds IMEA's weekly soybean harvest progress for Mato Grosso,
season 2025/26 (% of planted area harvested, state-wide). IMEA's bulletin comes out
weekly with data through the previous Thursday; `week_start_date` is the Friday
reference date of each bulletin.

Values were collected from press coverage of the IMEA weekly bulletins (the IMEA
site serves the numbers as PDF bulletins; press articles reproduce them):

| date | % harvested | source |
|------|-------------|--------|
| 2026-01-09 | 1.98 | Canal Rural / Projeto Soja Brasil |
| 2026-01-16 | 6.69 | CenárioMT |
| 2026-01-23 | 13.88 | derived: 24.97 (Jan 30) minus the reported 11.09 pp weekly advance |
| 2026-01-30 | 24.97 | Notícias Agrícolas |
| 2026-02-06 | 39.61 | Notícias Agrícolas |
| 2026-02-13 | 51.01 | ISTOÉ / Reuters |
| 2026-02-20 | 65.75 | Agrolink / Notícias Agrícolas |
| 2026-02-27 | 78.34 | ISTOÉ |
| 2026-03-06 | 89.15 | Canal Rural (reported 2026-03-13 as previous week) |
| 2026-03-13 | 96.42 | Notícias Agrícolas / Reuters |
| 2026-03-20 | 99.06 | ISTOÉ |

Caveat for the pitch: IMEA's series covers the whole state; our 7 demo fields are
clustered near Sorriso (Médio-Norte), one of the earlier-harvesting regions, so our
predicted curve is expected to run AHEAD of the state curve — the comparison is
about shape (onset, slope, saturation), not exact overlap.
