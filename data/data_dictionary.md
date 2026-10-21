# Canonical daily panel

Task 1 maps the verified HDX PortWatch CSV snapshot to the shared schema below. The source has 29 columns, including the uppercase spelling `ISO3`. Keep the raw CSVs unchanged.

| Canonical field | Source field | Type | Meaning |
|---|---|---|---|
| date | date | YYYY-MM-DD | Observation day from the published midnight UTC timestamp; no local-time shift |
| port_id | portid | string | Stable source port or terminal identifier; source name is not used as the key |
| country_iso3 | ISO3 | string | Uppercase source country code |
| import_tonnes | import | numeric | Published aggregate estimated inbound shipment volume, metric tonnes |
| export_tonnes | export | numeric | Published aggregate estimated outbound shipment volume, metric tonnes |
| portcalls | portcalls | numeric | Published total daily calls across container, dry bulk, general cargo, ro-ro and tanker categories |
| cargo_tonnes | import + export | numeric | Sum of published aggregate import and export; missing if either is unknown |

Unique key: `(port_id,date)`. The panel is sorted by port ID and ascending date. Port IDs must map to a single country across the snapshot. Missing keys, duplicate normalized keys, non-midnight dates, negative or non-finite required measurements and fractional call counts stop preparation for investigation. No arbitrary duplicate row is preferred. Source calendar columns `year`, `month` and `day` must agree with the timestamp.

## Calendar and missing values

Every port is reindexed from the snapshot's first through last date. Absent source records receive missing measurements, never zero. Only country metadata is carried onto those rows. Missing source records are listed in `results/missing_calendar_dates.csv`; source-field missingness is in `results/source_field_audit.csv`. A blank numeric CSV value means unknown. Numeric 0 means a zero reported by the source. No imputation, interpolation, clipping, zero deletion or outlier deletion is performed.

The audited snapshot has 594,720 source rows, 210 port/terminal IDs and 2,832 days, from 2019-01-01 through 2026-10-02. There are no absent calendar records or missing source measurements in this snapshot. The code preserves the missing-versus-zero distinction if either occurs in a later approved snapshot.

## Source columns retained in raw data

The source contains `date,year,month,day,portid,portname,country,ISO3`, followed by seven fields for each of the prefixes `portcalls`, `import` and `export`: the suffixes `_container`, `_dry_bulk`, `_general_cargo`, `_roro`, `_tanker`, `_cargo`, and the unsuffixed aggregate. This gives 29 source fields. `_cargo` is a subtotal and is not added to the individual categories or aggregate again.

The five disjoint ship-category call counts reconcile to `portcalls` in the audited snapshot. Published aggregate shipment volumes sometimes differ from sums of their five categories by up to four tonnes. The audit records these differences; the aggregate is retained and the cause is not asserted as verified. Port and country names are preserved in `data/ports_metadata.csv`. All source columns remain available in the immutable raw files.

`ports_metadata.csv:source_named_offshore_oil_terminal` is a descriptive flag for source names containing Offshore Oil Terminal. There are 44 such IDs in this snapshot, including seven of the eight entire-snapshot zero-cargo IDs. This label comes from source metadata and is not an independently verified classification or an eligibility filter. Coverage by this label is in `results/entity_coverage.csv`.

## Audit and selection fields

`results/port_audit.csv` describes the **full snapshot**: calendar days, known-cargo days, positive-cargo days, zero days, zero days with calls, cargo coverage and longest observed zero run. Its activity shares use known cargo days as the denominator and are not modelling groups.

`selected_ports.csv` uses **training dates only**: 2019-01-01 through 2024-12-31, or 2,192 calendar days. `train_calendar_days` is that denominator; `train_coverage` is known cargo days divided by it; `train_active_share` is positive cargo days divided by it. `train_active_share_observed` also reports the share among known cargo days, so missingness remains visible. The current candidate requires coverage=1 and active share>=0.2 (at least 439 active days). Activity groups are low for shares below 1/3, medium for [1/3,2/3), and high for >=2/3; these fixed descriptive bands are applied to training shares only. Retained low-activity ports also satisfy the 20% eligibility floor.

The file contains 137 IDs: 23 low-, 47 medium- and 67 high-activity. All 10 source countries remain represented. Every one of the 73 excluded IDs has its training counts and reason in `results/port_selection_audit.csv`; the full clean panel is unchanged. Country retention is in `results/country_retention.csv`. `rule_status` explicitly identifies the list as an unfrozen candidate. Date agreement was reported by Han; final eligibility-rule approval is separate and remains pending joint Task 2 review. The validation sensitivity compares this candidate with coverage-only eligibility using identical scoring keys.

`results/zero_runs.csv` contains contiguous observed-zero segments, their start/end, length, call diagnostics and snapshot-boundary flags. Missing cargo breaks a segment. Durations at snapshot boundaries are censored and do not establish total port inactivity outside the observed period. The >=28-day diagnostic does not determine eligibility.

## Provenance and timing

Source URLs, download metadata, estimated-tonne units, coverage, terms and individual SHA-256 values are recorded in the local manifest and `docs/portwatch_snapshot_manifest.json`. `experiment.json:data_snapshot_sha256` identifies the multi-file bundle; its hash definition is recorded alongside it. `results/data_audit.json:panel_sha256` identifies the separate cleaned CSV.

The timestamp is an observation label, not proof of publication availability. Historical origin-level release times and revision vintages are unavailable in the supplied files; same-day availability remains an experiment assumption requiring Task 2 review. TEU, tonnes, calls, trade value and measured terminal capacity are different quantities.
