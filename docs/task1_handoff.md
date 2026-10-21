# Task 1 handoff to Dinh and Hieu

Owner: Nguyen Thi Quynh Han. Assignment deadline: 25 October 2026. Branch: `task1-han`.

## Prepared outputs

The verified snapshot is the 18 October HDX download documented in `data_access.md`; no older five-country repackaging is combined with it. The clean panel is `data/ports_daily.csv`, with exact source mapping and missingness rules in `data/data_dictionary.md`. `results/data_audit.md` and `data_eda.md` document source checks, country coverage, zero days, long zero segments, aggregate/category differences and three EDA figures. The local `data/manifest.csv` records provenance; `experiment.json` records the multi-file snapshot hash. Raw and derived panels are not committed to Git.

The core target remains **total estimated cargo over t+1 through t+7**, where daily cargo is published import plus export in metric tonnes. This handoff adds no national trade, weather, oil, revenue or measured-capacity target. The 10 coastal Southeast Asian source countries are retained in the panel. Lao PDR is outside this core port forecast, consistent with the repository plan.

## Agreed calendar boundaries

On 20 October 2026, Han explicitly confirmed that both Dinh and Hieu agreed to the following dates. `experiment.json:time_split_agreement` records this as an agreement reported by Han; no direct message from either teammate is invented. The exact original agreement date is unknown. The Word proposal did not supply these cutoffs; its 2019-2024 auxiliary trade-data period is not their justification.

| Split | Observation/target period | Permitted origins with a complete 28-day history and 7-day target |
|---|---|---|
| Training | 2019-01-01 to 2024-12-31 | 2019-01-28 to 2024-12-24 |
| Validation | 2025-01-01 to 2025-12-31 | 2024-12-31 to 2025-12-24 |
| Test, reserved | 2026-01-01 to 2026-10-02 | 2025-12-31 to 2026-09-25 |

The origin on the last observation date of the preceding split predicts the first seven days of the next period, as required by `protocol.md`. Origins from 25 through 30 December at the train/validation and validation/test boundaries have crossing labels and must be excluded. Training selection uses all 2,192 observation days through 31 December 2024; the shorter supervised-training origin interval is a separate label-boundary restriction.

## Training-only candidate and exclusions

`data/selected_ports.csv` now contains **137 of 210** source IDs under the protocol's >=20% active-day candidate, with complete training cargo coverage. The threshold requires at least 439 positive-cargo days among the 2,192 training calendar days. No zero day is deleted. All 73 excluded IDs are retained in the full panel and have their training statistics and reasons in `results/port_selection_audit.csv`.

Activity groups use fixed, lower-inclusive one-third/two-thirds cuts on training active-day share: 23 low, 47 medium and 67 high. These are transparent descriptive bands, not validation-tuned group boundaries. `results/country_retention.csv` reports country counts; all 10 coastal source countries remain represented. The 137-port result was calculated from training observations and is not the earlier full-snapshot claim of 138 ports.

`results/port_selection_rules.json` records the exact candidate and snapshot hash. The split agreement permits candidate selection; it does not imply approval of the 20% rule, these group bands or validation findings. The candidate is explicitly **not frozen**.

## Validation sensitivity prepared for joint Task 2 review

`src/validate_port_rules.py` compares complete-coverage eligibility (210 ports) with the >=20% candidate (137 ports). It uses the shared protocol's three features and one fixed pooled multivariate linear diagnostic, plus seasonal naive as a reference. It does not produce Task 2's production `learning_table.csv` or full four-baseline comparison. All test-period measurements are discarded before any diagnostic feature or label is constructed.

Both candidates are scored on exactly **49,183 validation keys across 137 ports**. Coverage-only eligibility contributes 453,180 training rows; the 20% candidate contributes 295,646. The common validation set excludes 26,207 otherwise complete rows from the 73 ports outside the intersection. Calendar, history and target exclusions and candidate-specific training exclusions are recorded per key. Common-key hashes, model scaling/coefficients and source/panel hashes are in `results/eligibility_validation.json`.

| Eligibility rule | Linear validation MAE (tonnes) | RMSE (tonnes) | WAPE (%) |
|---|---|---|---|
| Complete coverage only | 58,964.8162 | 124,385.5547 | 16.7968 |
| Coverage plus >=20% activity | 58,956.3788 | 124,399.6590 | 16.7944 |

The 20% candidate has the lower primary metric, but its MAE advantage is only about 0.0143% and RMSE is slightly worse. It remains a candidate for joint review, not evidence of a robust improvement or a universal rule. The common cohort does not assess forecast quality for the extra low-activity ports retained by coverage-only eligibility. Seasonal-naive predictions are identical on common keys and cannot identify an eligibility winner. The full comparison, country/group/per-port metrics and interpretation limits are in `results/eligibility_validation.md` and its linked local outputs.

## Remaining completion and review steps

The four Task 1 output locations exist: the clean panel, candidate selected-port list, audit and English EDA. The technical preparation and independent validation sensitivity are ready to review. Task 1's final completion check still requires the joint decision on the rule and its freeze; the repository explicitly asks for validation comparison with Task 2 and handoff of frozen port rules.

1. Dinh and Hieu review/reproduce the candidate comparison, common keys, exclusions and information-cutoff assumption using their production workflow.
2. Record the actual joint eligibility decision, review evidence and freeze in the rules record. Do not change `frozen` merely because the date boundaries were approved.
3. Hand off the final selected-port list and frozen rules to Task 2. Reserve all test scoring until that decision and the model settings are frozen.
4. Submit the `task1-han` branch through a pull request into `main`. Another member must review it before any merge; the unresolved joint eligibility decision remains explicit in the handoff and rules record.

## Publication availability

Source labels are midnight UTC observation dates. The raw files do not contain historical publication times or revision vintages. The 16-day gap between the latest observation and the download date is descriptive, not an estimated historical release schedule. Confirm the information available at each forecast origin, or explicitly agree a conservative lag/scenario before operational claims. Revised historical data can overstate real-time performance.

## Verification and review

The preparation checks cover unknown measurements versus zero, absent dates, port isolation, duplicate/missing keys, invalid values, aggregate-only cargo, snapshot tampering and future-data invariance of eligibility/grouping. The unittest command is in the root README. Full real-data preparation has been run; actual counts, package versions, script hash and output hash are saved in the audit JSON.

The Task 1 diagnostic tests now include a hand-worked seven-day target, feature windows, port isolation, label boundaries, missing-window propagation, metrics, zero-denominator WAPE and real prediction-key reconciliation. Task 2 must preserve these checks in its production implementation. Passing this diagnostic suite does not imply that unimplemented production scripts have been tested or that joint review occurred.
