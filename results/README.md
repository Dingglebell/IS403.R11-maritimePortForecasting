# Experiment outputs

Task 1 audit and validation-only eligibility sensitivity results exist here. Task 2's production baseline comparison and final test results do not yet exist. Large outputs are ignored by default; explicitly add only reviewed small results, for example `git add -f results/metrics.csv`.

Task 1 generates `data_audit.md`, `data_audit.json`, source-field, port and country checks, observed-zero-run diagnostics, three figures, `country_retention.csv` and `port_selection_rules.json`. Full-snapshot activity shares are descriptive and must not be reused as training-defined model groups. Training-based candidate selection was run after Han confirmed Dinh/Hieu's agreement to the dates. The current candidate keeps 137 IDs across all 10 coastal countries.

`eligibility_validation.md` and `.json` document the controlled validation comparison; `eligibility_validation_metrics.csv`, `eligibility_country_retention.csv`, `eligibility_origin_counts.csv` and `eligibility_exclusion_summary.csv` are compact review tables. Per-port/group metrics, predictions, common-key lists, per-key exclusions, `port_selection_audit.csv`, `zero_runs.csv` and derived panels remain local. The selected 20% candidate has only a very small MAE advantage in the fixed linear diagnostic; final review and rule freezing remain joint work with Task 2. No test score is generated.

Use the prediction schema in docs/protocol.md. Store one row per model, feature set, split, port and origin. Keep validation outputs separate from the final test outputs. Record model settings, seeds, versions, dataset hash and the commit used for each run.

Suggested metric columns: model, feature_set, split, group_type, group_value, n_rows, n_ports, MAE, RMSE, WAPE_pct. Use NA for undefined WAPE. State units and sample counts on figures; export legible figures for the English paper and slides.
