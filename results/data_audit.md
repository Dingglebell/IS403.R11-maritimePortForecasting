# Data audit (generated)

Source: IMF PortWatch via HDX, locally obtained/verified 18 October 2026. This is not verified as byte-identical to the group's earlier 12 October copy. Individual provenance is in `data/source_manifest.csv`; blank download timestamps were not recorded, not invented.

- Snapshot SHA256: `fb4eee5b71de5692334abc45fadbee522fc32572e30ded15f2e6daeade137070` (sorted filename + TAB + SHA256 + LF, UTF-8).
- Clean CSV SHA256: `f8c402ed90ad70d851b0cf82e4c57d1d810cc3faa3bac958efd4bf68dd96d9b6`.
- Rows: 594,720; source rows: 594,720; port/terminal IDs: 210; countries: 10.
- Dates: 2019-01-01 to 2026-10-02; unique port/date keys verified.
- Added missing calendar rows: 0; unknown cargo: 0; required negative/invalid/nonfinite values: none (cleaner rejects them).
- Observed zero cargo: 322,534/594,720 (54.2329%); positive cargo: 272,186.
- Zero cargo with positive calls: 30,228 (9.3720% of observed zeros).
- Zero runs >=28 days: 1,173, across 97 IDs; 622 such runs contain positive calls. These are review flags, not evidence of missingness. Boundary runs are censored.
- Source names containing Offshore Oil Terminal: 44; no name-based exclusions.
- No zero removal, imputation, clipping, outlier deletion or deduplication. Required invalid input stops cleaning. All saved panel values matched a fresh reconstruction from raw CSVs.
- Training-only illustration: if zero days were deleted, the next seven positive observations would span more than seven calendar days in 52.7303% of 205,872 eligible positive-origin windows; median 8 days, maximum 1880. This is an invalid change of target, not an alternative scored forecast. Per-port detail: `zero_calendar_distortion.csv`.

## Country coverage (full snapshot; descriptive only)

| country_iso3 | ports | rows | known | zero_days | zero_days_with_calls | zero_pct |
| --- | --- | --- | --- | --- | --- | --- |
| BRN | 2 | 5664 | 5664 | 3367 | 154 | 59.4456 |
| IDN | 101 | 286032 | 286032 | 153267 | 11526 | 53.5839 |
| KHM | 1 | 2832 | 2832 | 272 | 17 | 9.6045 |
| MMR | 2 | 5664 | 5664 | 2878 | 44 | 50.8121 |
| MYS | 41 | 116112 | 116112 | 65234 | 1694 | 56.1820 |
| PHL | 26 | 73632 | 73632 | 48086 | 11366 | 65.3058 |
| SGP | 3 | 8496 | 8496 | 94 | 32 | 1.1064 |
| THA | 13 | 36816 | 36816 | 19516 | 1651 | 53.0096 |
| TLS | 3 | 8496 | 8496 | 7779 | 30 | 91.5607 |
| VNM | 18 | 50976 | 50976 | 22041 | 3714 | 43.2380 |

## Source-field checks

| field | missing | invalid_numeric | negative | nonfinite |
| --- | --- | --- | --- | --- |
| date | 0 | 0 | 0 | 0 |
| year | 0 | 0 | 0 | 0 |
| month | 0 | 0 | 0 | 0 |
| day | 0 | 0 | 0 | 0 |
| portid | 0 | 0 | 0 | 0 |
| portname | 0 | 0 | 0 | 0 |
| country | 0 | 0 | 0 | 0 |
| ISO3 | 0 | 0 | 0 | 0 |
| portcalls_container | 0 | 0 | 0 | 0 |
| portcalls_dry_bulk | 0 | 0 | 0 | 0 |
| portcalls_general_cargo | 0 | 0 | 0 | 0 |
| portcalls_roro | 0 | 0 | 0 | 0 |
| portcalls_tanker | 0 | 0 | 0 | 0 |
| portcalls_cargo | 0 | 0 | 0 | 0 |
| portcalls | 0 | 0 | 0 | 0 |
| import_container | 0 | 0 | 0 | 0 |
| import_dry_bulk | 0 | 0 | 0 | 0 |
| import_general_cargo | 0 | 0 | 0 | 0 |
| import_roro | 0 | 0 | 0 | 0 |
| import_tanker | 0 | 0 | 0 | 0 |
| import_cargo | 0 | 0 | 0 | 0 |
| import | 0 | 0 | 0 | 0 |
| export_container | 0 | 0 | 0 | 0 |
| export_dry_bulk | 0 | 0 | 0 | 0 |
| export_general_cargo | 0 | 0 | 0 | 0 |
| export_roro | 0 | 0 | 0 | 0 |
| export_tanker | 0 | 0 | 0 | 0 |
| export_cargo | 0 | 0 | 0 | 0 |
| export | 0 | 0 | 0 | 0 |

## Category reconciliation

| measure | total_vs_5_categories_differing_rows | max_abs_difference | cargo_subtotal_vs_4_categories_differing_rows | max_abs_subtotal_difference |
| --- | --- | --- | --- | --- |
| portcalls | 0 | 0 | 0 | 0 |
| import | 69981 | 4 | 38947 | 3 |
| export | 64500 | 4 | 35987 | 3 |

Keep published totals. Do not sum subtotals and categories together. The cause of small cargo discrepancies is unverified; they are not silently corrected.

## Entire-snapshot zero-cargo entities

| port_id | port_name | country_iso3 | source_named_offshore_oil_terminal |
| --- | --- | --- | --- |
| fso111 | Malaysia - Offshore Oil Terminal 14 | MYS | True |
| fso121 | Malaysia - Offshore Oil Terminal 7 | MYS | True |
| fso122 | Malaysia - Offshore Oil Terminal 8 | MYS | True |
| fso123 | Malaysia - Offshore Oil Terminal 9 | MYS | True |
| fso91 | Indonesia - Offshore Oil Terminal 14 | IDN | True |
| fso93 | Indonesia - Offshore Oil Terminal 2 | IDN | True |
| fso99 | Indonesia - Offshore Oil Terminal 8 | IDN | True |
| port2154 | Muntok | IDN | False |

These are descriptive retrospective flags, never training eligibility criteria. Neither zero estimates nor positive calls establish true cargo throughput.

## Training-only country retention

| country_iso3 | source_ports | retained | active20 |
| --- | --- | --- | --- |
| BRN | 2 | 2 | 1 |
| IDN | 101 | 101 | 71 |
| KHM | 1 | 1 | 1 |
| MMR | 2 | 2 | 1 |
| MYS | 41 | 41 | 24 |
| PHL | 26 | 26 | 14 |
| SGP | 3 | 3 | 3 |
| THA | 13 | 13 | 7 |
| TLS | 3 | 3 | 1 |
| VNM | 18 | 18 | 14 |

The handoff keeps complete-training-coverage ports; the 20% active-day filter is a sensitivity candidate. Both count training calendar days, including genuine zeros. Joint Task 2 review is pending. See `docs/zero_handling.md` for validation evidence and `data/data_dictionary.md` for field meanings.
