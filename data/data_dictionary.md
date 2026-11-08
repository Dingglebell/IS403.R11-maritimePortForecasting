# Data dictionary — Task 1

Owner: Nguyễn Thị Quỳnh Hân. Verified against the 18 October 2026 local IMF PortWatch/HDX snapshot. This dictionary covers raw fields, the clean panel, port-selection metadata and validation outputs. CSVs use UTF-8, comma separators, decimal points and blank cells for unknown numeric values. Zero is an observed source value, never a substitute for missing data.

## 1. Clean daily panel: `ports_daily.csv`

One row per **port/terminal ID and calendar day**, sorted by `port_id,date`. The seven columns below appear in this exact order. Units are estimated metric tonnes (1 tonne = 1,000 kg), not TEU, money or measured port capacity.

| Column | Raw source / derivation | Type and valid values | Definition / missing rule |
|---|---|---|---|
| date | date | ISO date YYYY-MM-DD, required | Midnight UTC observation label converted to calendar date without local-time shift. Not a publication timestamp. |
| port_id | portid | Nonblank string, required | Source port or terminal identifier; names are not unique keys. One ID must map to one country. |
| country_iso3 | ISO3 | Three uppercase letters, required | Source country code. Metadata may be carried onto inserted calendar rows. |
| import_tonnes | import | Finite number >=0, or blank | Published aggregate estimated incoming shipment volume that day. |
| export_tonnes | export | Finite number >=0, or blank | Published aggregate estimated outgoing shipment volume that day. |
| portcalls | portcalls | Integer-valued count >=0, or blank | Published aggregate daily calls across the five source vessel categories below; a call is not a tonne. |
| cargo_tonnes | import + export | Finite number >=0, or blank | Sum the two published aggregates once; blank if either component is unknown. |

The cleaner rejects missing keys, duplicate normalized port/day keys, country conflicts, non-midnight timestamps, negative/nonfinite/nonnumeric required values and fractional calls. It reindexes each ID onto the snapshot's complete daily calendar; missing measurements stay blank. No zero, extreme value or port is removed from this full panel. Source `year/month/day` agreement is checked by the audit stage.

## 2. Raw country CSVs: all 29 source fields

Field spellings and case are preserved. The raw files are immutable. The clean panel retains published totals; all component detail remains available in raw data.

| Raw field | Type / unit | Definition and treatment |
|---|---|---|
| date | ISO8601 UTC timestamp | Daily observation label; mapped to `date`. |
| year | integer, year | Calendar year, must match date; redundant in clean panel. |
| month | integer, 1–12 | Calendar month, must match date. |
| day | integer, 1–31 | Day of month, must match date. |
| portid | string | Mapped to `port_id`. |
| portname | string | Source display name, retained in `ports_metadata.csv`. |
| country | string | Source country name, retained in metadata. |
| ISO3 | string | Mapped to `country_iso3`; uppercase field name in source. |
| portcalls_container | count/day | Container-vessel category calls. |
| portcalls_dry_bulk | count/day | Dry-bulk-vessel category calls. |
| portcalls_general_cargo | count/day | General-cargo-vessel category calls. |
| portcalls_roro | count/day | Roll-on/roll-off-vessel category calls. |
| portcalls_tanker | count/day | Tanker-category calls. |
| portcalls_cargo | count/day | Cargo subtotal, excluding tankers; do not add again to individual categories. |
| portcalls | count/day | Published aggregate calls; mapped directly. |
| import_container | estimated tonnes/day | Incoming shipment volume for container vessels. |
| import_dry_bulk | estimated tonnes/day | Incoming shipment volume for dry-bulk vessels. |
| import_general_cargo | estimated tonnes/day | Incoming shipment volume for general-cargo vessels. |
| import_roro | estimated tonnes/day | Incoming shipment volume for ro-ro vessels. |
| import_tanker | estimated tonnes/day | Incoming shipment volume for tankers. |
| import_cargo | estimated tonnes/day | Incoming cargo subtotal excluding tankers. |
| import | estimated tonnes/day | Published incoming aggregate; mapped to `import_tonnes`. |
| export_container | estimated tonnes/day | Outgoing shipment volume for container vessels. |
| export_dry_bulk | estimated tonnes/day | Outgoing shipment volume for dry-bulk vessels. |
| export_general_cargo | estimated tonnes/day | Outgoing shipment volume for general-cargo vessels. |
| export_roro | estimated tonnes/day | Outgoing shipment volume for ro-ro vessels. |
| export_tanker | estimated tonnes/day | Outgoing shipment volume for tankers. |
| export_cargo | estimated tonnes/day | Outgoing cargo subtotal excluding tankers. |
| export | estimated tonnes/day | Published outgoing aggregate; mapped to `export_tonnes`. |

In this snapshot, `portcalls` equals the five category counts and `portcalls_cargo` equals the four non-tanker categories on every row. Import/export aggregates differ from category sums by up to four tonnes (subtotals by up to three); `results/category_reconciliation.csv` records the discrepancies. Rounding is a possible explanation, not a verified cause. Never overwrite published totals or add overlapping totals/subtotals. Ship categories are source categories, not independently reclassified vessel records.

## 3. Scope and codes

| ISO3 | Country | ISO3 | Country |
|---|---|---|---|
| BRN | Brunei Darussalam | MMR | Myanmar |
| KHM | Cambodia | PHL | Philippines |
| IDN | Indonesia | SGP | Singapore |
| MYS | Malaysia | THA | Thailand |
| TLS | Timor-Leste | VNM | Viet Nam |

There are 210 port/terminal IDs and 594,720 daily rows, 2019-01-01–2026-10-02. Lao PDR remains in the broader 11-country proposal but has no coastal port series in this core panel. Source names contain `Offshore Oil Terminal` for 44 IDs; this is a descriptive name flag, not a verified classification or exclusion rule.

## 4. Port metadata and selection

`ports_metadata.csv` has `port_id,port_name,country,country_iso3,source_named_offshore_oil_terminal`. The last field is Boolean, computed by case-insensitive name matching. All metadata have one row per ID.

`selected_ports.csv` contains the recommended handoff cohort. `results/port_selection_audit.csv` has the same fields for every source ID, including exclusions and the alternative 20% rule. Statistics use **2019-01-01–2024-12-31 only (2,192 calendar days)**. A port list is not permission to remove zero days.

| Field | Type / unit | Meaning |
|---|---|---|
| port_id, country_iso3, port_name | strings | Source identity and display metadata. |
| train_known_days | integer days | Training days with known cargo. |
| train_active_days | integer days | Training days with cargo strictly greater than zero. |
| train_calls_known_days | integer days | Training days with known calls. |
| train_calendar_days | integer days | Full agreed training calendar length, including zero and missing days. |
| train_coverage | fraction 0–1 | train_known_days / train_calendar_days. |
| train_active_share | fraction 0–1 | train_active_days / train_calendar_days. |
| train_active_share_observed | fraction 0–1, or blank | train_active_days / train_known_days; blank for no known days. |
| activity_group | low / medium / high | Training active share <1/3; [1/3,2/3); >=2/3. Fixed descriptive bands. |
| selected | Boolean | Complete training cargo **and calls** coverage; no activity floor for the handoff recommendation. |
| candidate_active20 | Boolean | selected AND train_active_share >=0.20; at least 439 positive days in this snapshot. |
| reason | string | Explicit inclusion/exclusion reason for handoff rule. |
| active20_reason | string | Explicit inclusion/exclusion reason for 20% sensitivity. |
| rule_status | string | Task 1 recommendation, pending joint Task 2 review; not fabricated team approval. |

The default handoff retains 210 IDs; 137 meet the 20% candidate. The full panel is unchanged under either rule. Review evidence in `docs/zero_handling.md` before freezing the shared modelling cohort.

## 5. Zero diagnostics and validation fields

`results/port_audit.csv` is descriptive over the full snapshot: `days` is calendar rows, `known` is known-cargo days, `positive_days`, `zero_days`, `zero_days_with_calls`, `zero_pct=100*zero_days/known`, and `longest_zero_run`. These full-snapshot fields do not set selection/group rules. `results/zero_runs.csv` lists `port_id,country_iso3,start,end,days,days_with_calls,calls,left_censored,right_censored`. Runs break at missing cargo or calendar gaps; `calls` sums known call counts. Censor flags mark a run touching the available series boundary; its true duration may be longer. A >=28-day run is a review flag, not an imputation trigger.

Validation origin `t` uses `cargo_7d=sum(V[t-6:t])`, `calls_7d=sum(calls[t-6:t])`, `cargo_mean_28d=mean(V[t-27:t])`. Units: tonnes, calls, tonnes/day. `y_true=sum(V[t+1:t+7])` is tonnes per seven-calendar-day target. `origin_date`, `target_start` and `target_end` are ISO dates. `y_pred` has the same units as `y_true`. `split` is always `validation` in the diagnostic prediction file.

Prediction identifiers include `policy,model,clipping,port_id,origin_date`; `feature_set` identifies `all_three` or the cargo-only reference. Policy meanings, common cohorts and training exclusions are defined in `docs/zero_handling.md`. Labels are original observations for every policy. Missing windows are excluded, never filled with zero. Prediction files are local, ignored artifacts.

Metrics: `n` is scored origins, `ports` is distinct IDs, `MAE` and `RMSE` are tonnes/target, `macro_port_MAE` averages per-port MAE, `bias=mean(predicted-actual)` in tonnes, `WAPE_pct=100*sum(abs(error))/sum(actual)` (blank if total actual is zero), and `zero_actual_windows` counts all-zero seven-day labels. `cohort` is all 210 eligible IDs or the common 137-ID active20 subset. `weekly_phase` is `(origin-train_end) mod 7`, evaluated separately for all seven offsets.

## 6. Provenance and measurement limits

`source_manifest.csv` records each filename, stable source/download URL, verification time, recorded download time (blank if unavailable), SHA256, byte size, row/port counts, date coverage and source terms URL. It intentionally excludes temporary signed redirects. The original snapshot metadata remain local. `results/task1_run.json` records config/code/panel/key hashes, fitted coefficients and tested versions; it is the single compact machine-readable run record.

Source: [IMF PortWatch](https://portwatch.imf.org/), distributed through the [HDX source datasets](https://data.humdata.org/dataset/brunei-darussalam-daily-port-activity-data-and-shipment-estimates). [Arslanalp et al. (2025), section 2](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025093-print-pdf.pdf) describes estimated shipments and revision/measurement limitations. Published zero estimates are not independently verified physical inactivity. Historical release timestamps/vintages are absent, so the diagnostic assumes same-day observation availability and is not a proven real-time backtest. No capacity, congestion or cost-saving claim follows directly from these data.
