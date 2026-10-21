# Task 1 data audit

Audit generated at 2026-10-20T02:30:34.938031+00:00. Owner: Nguyen Thi Quynh Han. Status: panel and descriptive audit prepared; final eligibility decisions require joint validation review.

## Snapshot and canonical panel

The verified snapshot contains 594,720 source rows for 210 port/terminal IDs in 10 coastal Southeast Asian countries. Source observations span 2019-01-01 to 2026-10-02 (2832 calendar days). Local download date(s): 2026-10-18, independently of the group's reported 12 October copy. Matching preliminary counts does not establish byte identity. The SHA-256 bundle is `fb4eee5b71de5692334abc45fadbee522fc32572e30ded15f2e6daeade137070`; its definition and individual file hashes are in `docs/portwatch_snapshot_manifest.json`.

The canonical panel has 594,720 rows with unique `(port_id,date)` keys, sorted by port and date. The calendar check found 0 absent source records. Missing cargo measurements: 0. Negative numeric source measurements: 0. Invalid numeric source values: 0. No original row was deleted and no measurement was imputed, clipped or replaced. If another snapshot contains invalid keys, duplicate keys or invalid required measurements, preparation stops for investigation.

There are 322,534 observed zero-cargo days out of 594,720 known cargo days (54.2329%). The measured proportion rounds to the preliminary 54.2%. The positive-cargo count is 272,186. Missing cargo is outside this zero-rate denominator. On 30,228 zero-cargo days, port calls are positive (9.37% of observed zeros). A reported zero is retained as an observed source value; it is not proof of no vessel activity or of a confirmed reporting gap.

Source mapping: `date -> date`, `portid -> port_id`, `ISO3 -> country_iso3`, `import -> import_tonnes`, `export -> export_tonnes`, and `portcalls -> portcalls`. Cargo is the sum of the two published aggregate shipment columns, in estimated metric tonnes. Category columns and subtotals are not added again. UTC midnight source labels are retained as calendar dates without a conversion to local dates. Detailed mappings and missingness rules are in `data/data_dictionary.md`.

## Country coverage and zeros

| country_iso3 | ports | calendar_rows | zero_days | zero_pct | zero_days_with_calls |
| --- | --- | --- | --- | --- | --- |
| BRN | 2 | 5664 | 3367 | 59.45 | 154 |
| IDN | 101 | 286032 | 153267 | 53.58 | 11526 |
| KHM | 1 | 2832 | 272 | 9.60 | 17 |
| MMR | 2 | 5664 | 2878 | 50.81 | 44 |
| MYS | 41 | 116112 | 65234 | 56.18 | 1694 |
| PHL | 26 | 73632 | 48086 | 65.31 | 11366 |
| SGP | 3 | 8496 | 94 | 1.11 | 32 |
| THA | 13 | 36816 | 19516 | 53.01 | 1651 |
| TLS | 3 | 8496 | 7779 | 91.56 | 30 |
| VNM | 18 | 50976 | 22041 | 43.24 | 3714 |

These are full-snapshot descriptive counts, not training-based eligibility or retention. All source countries and ports are retained in the clean panel. Candidate country retention, when selection is run, is reported in the handoff section below.

Observed zero-day shares range from 1.11% in SGP to 91.56% in TLS. The pooled zero rate masks substantial country heterogeneity; later evaluation should retain country and port breakdowns.

## Long zero runs and possible gaps

Observed zero runs: 65,053. Runs lasting at least 28 days: 1,173, involving 97 ports. Of those long runs, 622 contain at least one positive-call day. The 28-day flag is a diagnostic matching the proposed four-week feature history, not a port exclusion rule. Entire-snapshot zero-cargo ports: 8. Missing days and missing measurements break a zero run.

Retaining zeros matters for the study target: the next seven calendar days must include observed zero days. Dropping them would compress the calendar, change the forecast horizon and train only on a conditional positive-activity sample. Missing observations instead make the corresponding complete-window sample unavailable under the protocol. This preparation neither deletes zeros nor substitutes a zero for an unknown observation.

The ten longest runs are shown below. Runs touching a snapshot boundary are censored: their recorded durations cover only the observed segment. Boundary flags are retained in the run table. A long run with calls is a priority for source review; the aggregate fields alone cannot distinguish genuinely small/zero estimated shipments, estimation limitations and AIS/reporting gaps. No run has been relabelled missing, deleted or declared erroneous without independent evidence. Full run diagnostics are in `zero_runs.csv`; the >=28-day subset is in `long_zero_runs.csv`.

Source names explicitly label 44 of the 210 IDs as Offshore Oil Terminals. They account for 7 of the 8 entire-snapshot zero-cargo IDs. Other entire-snapshot zero IDs and source names: port2154 (Muntok). This is a source-metadata classification, not an independently validated asset taxonomy or an explanation of AIS/volume estimation failures. The descriptive coverage by source label is saved in `entity_coverage.csv`. No source-label or full-snapshot-zero filter is applied to select modelling ports.

| port_id | country_iso3 | start_date | end_date | days | days_with_positive_calls |
| --- | --- | --- | --- | --- | --- |
| fso111 | MYS | 2019-01-01 | 2026-10-02 | 2832 | 3 |
| fso121 | MYS | 2019-01-01 | 2026-10-02 | 2832 | 0 |
| fso122 | MYS | 2019-01-01 | 2026-10-02 | 2832 | 0 |
| fso123 | MYS | 2019-01-01 | 2026-10-02 | 2832 | 0 |
| fso91 | IDN | 2019-01-01 | 2026-10-02 | 2832 | 0 |
| fso93 | IDN | 2019-01-01 | 2026-10-02 | 2832 | 2 |
| fso99 | IDN | 2019-01-01 | 2026-10-02 | 2832 | 1 |
| port2154 | IDN | 2019-01-01 | 2026-10-02 | 2832 | 11 |
| fso95 | IDN | 2019-04-27 | 2026-10-02 | 2716 | 10 |
| fso97 | IDN | 2019-01-01 | 2025-12-07 | 2533 | 38 |

## Aggregate and category consistency

| source_total | complete_rows | different_from_category_sum | max_absolute_difference |
| --- | --- | --- | --- |
| portcalls | 594720 | 0 | 0.0 |
| import | 594720 | 69981 | 4.0 |
| export | 594720 | 64500 | 4.0 |

Small shipment differences are compatible with independently rounded or truncated estimates, but the exact mechanism is not established. Published aggregate import/export values remain authoritative for this study. No repair is made by adding a subtotal and its components together. Port-call totals are checked against the five disjoint source ship categories.

## Figures

![Country cargo history](figures/cargo_history.png)

Monthly mean daily cargo is computed from complete country-day totals. October 2026 has only two observed days and must not be compared as a full monthly total.

![Descriptive activity rates](figures/activity_rates.png)

Activity rates here describe data quality and heterogeneity. They do not assign low/medium/high model groups; those groups must use training observations only.

![Cargo versus calls](figures/cargo_vs_calls.png)

All complete cargo/call pairs are included in log-transformed density bins. This plot retains zeros and does not establish a causal relation between vessel calls and estimated cargo.

## Exclusions and handoff

No source row or port is excluded from preparation. Non-canonical source columns remain in the immutable raw CSVs; port names are retained in `data/ports_metadata.csv`. No national trade, weather or oil series is joined. Lao PDR has no port series in the core panel, as specified by the repository scope.

The recorded time boundaries are training 2019-01-01 through 2024-12-31, validation 2025-01-01 through 2025-12-31, and test 2026-01-01 through 2026-10-02. Han reported Dinh and Hieu's agreement on 20 October 2026. The supplied Word proposal is not the source of these exact cutoffs.

The current candidate retains 137 of 210 source IDs using only 2192 training calendar days. It requires cargo coverage >= 100% and a positive-cargo share >= 20%. Every excluded ID and reason is in `results/port_selection_audit.csv`. Observed zeros remain in all retained ports' histories and targets; no date is removed because it has zero cargo. The fixed low/medium/high bands have lower-inclusive cuts at [0.3333333333333333, 0.6666666666666666]; group counts are {'high': 67, 'low': 23, 'medium': 47}. The bands are descriptive design choices applied to training shares, not thresholds fitted on future data.

| country_iso3 | candidate_ports | retained_ports | excluded_ports |
| --- | --- | --- | --- |
| BRN | 2 | 1 | 1 |
| IDN | 101 | 71 | 30 |
| KHM | 1 | 1 | 0 |
| MMR | 2 | 1 | 1 |
| MYS | 41 | 24 | 17 |
| PHL | 26 | 14 | 12 |
| SGP | 3 | 3 | 0 |
| THA | 13 | 7 | 6 |
| TLS | 3 | 1 | 2 |
| VNM | 18 | 14 | 4 |

Country retention describes this candidate only. The rule remains unfrozen pending the joint Task 2 validation review. `results/eligibility_validation.md`, when generated by the documented validation command, records the independent sensitivity check for that review.

The supplied proposal describes PortWatch trends over 2019-2026 and 2019-2024 for auxiliary national trade data; it gives no explicit train/validation/test cutoffs. The repository requires agreement with Dinh and Hieu before selecting ports. A 20% active-day threshold remains a candidate. Compare candidate eligibility rules jointly with Task 2 on validation MAE and an unchanged intersection of valid port-origin keys; retain zeros in every candidate. Do not compare scores from different evaluation populations or use test results to choose a rule. This preparation report contains no validation or test scores; the separate validation-only diagnostic supports the joint review.

## Availability and interpretation limits

The local HDX metadata identifies weekly updates; this snapshot ends 16 calendar days before its earliest local download date. That observed snapshot gap is not a verified historical release lag. Origin-level publication timestamps and revision vintages are unavailable, so same-day availability through t is not established. Task 2 must record an information-cutoff convention before claiming an operational backtest. Historical revised data can be optimistic relative to data available in real time.

IMF describes AIS-derived shipments as estimates and notes that source-data updates, methodology changes and coverage changes can cause revisions ([IMF Working Paper 25/93, section 2](https://www.elibrary.imf.org/view/journals/001/2025/093/article-A001-en.xml)). Cargo is neither revenue nor measured terminal capacity. Forecasts may inform resource planning; congestion, utilisation or savings need independent operational evidence.

## Reproduction

Run the preparation command documented in the root README. The audit JSON records package versions, the preparation-script hash, snapshot hash and output-panel hash. Raw files and derived panels remain ignored by Git. Review small result tables and figures explicitly before adding them to a pull request.
