# Task 1 eligibility validation sensitivity

Status: diagnostic complete; joint Task 2 review and rule freeze pending. This is a reproducible Task 1 handoff, not a claim that Task 2 owners have reviewed results or completed their production learning table.

## Prespecified comparison

The user reported Dinh and Hieu's agreement to train on 2019-01-01 through 2024-12-31, validate on 2025-01-01 through 2025-12-31 and reserve 2026-01-01 through 2026-10-02 for test. Candidate definitions were recorded before this run: complete training cargo coverage alone, versus the same coverage plus positive cargo on at least 20% of training calendar days. Both retain all observed zeros. Eligibility and the one-third/two-thirds activity bands use training observations only. No source-name filter or full-snapshot activity share determines eligibility.

For a controlled pooled-training comparison, the diagnostic uses the shared protocol's fixed multivariate linear regression with an intercept. Inputs are cargo sum and calls sum from t-6 through t and mean cargo from t-27 through t. The target is one cargo total from t+1 through t+7. Feature scaling is fitted on each candidate's training rows only. Predictions are not clipped; the same setting is used for both candidates. Seasonal naive, equal to cargo_7d, is a reference: its identical predictions on shared rows cannot identify an eligibility winner.

## Common evaluation population and exclusions

All models and both candidates use exactly 49,183 validation origins across 137 ports, with complete history and future labels. Common-key SHA-256: `bc3917317eef025f673126c4094d4545d0bd7dd82ee4fa83d7ed25d12c881aa5`. Validation origins run from 2024-12-31 through 2025-12-24; target dates stay inside calendar 2025. Training origins require target_end <= 2024-12-31; validation origins require origin >= 2024-12-31 and target_end <= 2025-12-31. The initial 28-day history and crossing-boundary exclusions are explicit. Past feature history may precede the validation boundary.

| eligibility_rule | eligible_ports | training_rows | common_validation_rows | validation_rows_excluded_by_common_set |
| --- | --- | --- | --- | --- |
| coverage_only | 210 | 453180 | 49183 | 26207 |
| active_20pct | 137 | 295646 | 49183 | 26207 |

Port rules can change training rows but cannot change these scoring keys. All candidate-rejected ports and training statistics can be reconstructed from `port_selection_audit.csv` and the two thresholds; the complete common key list is `eligibility_validation_keys.csv`. `eligibility_origin_exclusions.csv` records calendar/window exclusions and validation keys outside the common cohort; `eligibility_exclusion_summary.csv` summarizes them. `eligibility_training_exclusions.csv` separately records every complete training key rejected by each candidate's port rule. `eligibility_country_retention.csv` records every country's source, retained and common-evaluation port counts for both candidates. Zero targets remain in scoring, including WAPE's numerator.

| split | exclusion_reason | rows |
| --- | --- | --- |
| excluded | origin_reserved_for_test | 210 |
| excluded | target_beyond_validation_end | 1260 |
| excluded | target_crosses_train_validation_boundary | 1260 |
| train | incomplete_past_window | 5670 |
| validation | outside_common_training_eligibility_set | 26207 |

## Validation results

| eligibility_rule | model | n_rows | n_ports | MAE | RMSE | WAPE_pct | macro_port_MAE | zero_actual_windows | negative_predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| coverage_only | multivariate_linear_regression | 49183 | 137 | 58964.8162 | 124385.5547 | 16.7968 | 58964.8162 | 1827 | 811 |
| coverage_only | seasonal_naive | 49183 | 137 | 74370.4508 | 157772.8545 | 21.1853 | 74370.4508 | 1827 | 0 |
| active_20pct | multivariate_linear_regression | 49183 | 137 | 58956.3788 | 124399.6590 | 16.7944 | 58956.3788 | 1827 | 1069 |
| active_20pct | seasonal_naive | 49183 | 137 | 74370.4508 | 157772.8545 | 21.1853 | 74370.4508 | 1827 | 0 |

MAE and RMSE are tonnes per seven-day target; WAPE is a percentage computed from sums, with NA for a zero actual-total denominator. Macro-port MAE weights ports equally. Country, training-activity and per-port breakdowns are in `eligibility_validation_breakdown.csv`. Separate prediction files use the protocol's exact ten-column schema; all rows have split=validation. No final test prediction or score is generated.

The lower validation MAE in the fixed linear diagnostic recommends **active_20pct** for joint review. Relative to coverage-only eligibility, the 20% candidate changes MAE by -8.4374 tonnes (-0.0143%) and RMSE by 14.1043 tonnes. The MAE difference is very small and RMSE need not favour the same candidate; this is not evidence of a robust or statistically established improvement. Seven-day targets at consecutive origins overlap, so observations are dependent and summed targets are not distinct weekly trade totals.

This comparison is not evidence that the same rule wins for RF/HGB, every feature set or ports outside the common cohort. The common cohort omits lower-training-activity ports excluded by the 20% candidate, so these scores cannot establish forecast quality for those additional ports. Country retention must be considered alongside validation error. The final rule remains unfrozen until Task 2 reviews and reproduces the comparison; dates alone do not imply agreement to this recommendation.

## Limits and handoff

This diagnostic assumes observations through t are available, as in the shared protocol. Historical publication timestamps and revision vintages are unavailable. It is a retrospective same-day-availability scenario, not a verified operational backtest; Task 2 must confirm or explicitly revise that convention. The implementation discards all measurements after 2025-12-31 before constructing any feature or label. Test values do not enter fitting, thresholds, model settings or scoring. Feature and metric boundary checks are exercised by the unit tests.

Joint review should verify common keys, denominators, exclusions, information availability and the recommendation before freezing the selection rules. Task 2's production scripts and full four-baseline comparison remain its owners' deliverables. No messages or approvals from Task 2 owners are fabricated here. Large prediction/key tables stay local and ignored by Git.
