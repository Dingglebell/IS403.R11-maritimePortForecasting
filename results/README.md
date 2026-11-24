# Experiment outputs

Task 1 audit and controlled validation results exist here. Start with `data_audit.md` and `zero_validation.md`; interpretation is in `docs/zero_handling.md`. `zero_policy_metrics.csv` includes overall, target, country, activity, port and seven weekly-phase results. `paired_block_sensitivity.csv` records paired date-block estimates. `task1_run.json` is the single compact machine-readable record of hashes, versions and coefficients. Figures are in `figures/`. No test scores exist.

Task 2's four-baseline validation comparison is in `baseline_validation.md` and `baseline_metrics.csv`. Split boundaries/counts are in `task2_split_summary.csv`; provenance and code/table/key hashes are in `task2_run.json`. Reproduce these with `python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv`. Large learning, prediction and exclusion files stay local. The final working output uses the common nonnegative rule; the raw sensitivity is also reported.

Step 2's independent feature/split review is in `task2_feature_review.md`. `task2_feature_checks.csv` records the full-table comparisons; `task2_handcheck_summary.csv` and `task2_boundary_examples.csv` provide concrete review examples. Reproduce them with `python src/features.py --panel data/da_xu_ly/ports_daily.csv` followed by `python src/check_features.py`. The combined completion review is recorded in `docs/task2_completion.md`.

Task 3's RF/HGB validation results are in `model_validation_metrics.csv` (chosen setting per model and feature set, raw and nonnegative), `model_candidates.csv` (every grid candidate) and `model_config.json` (grids, chosen settings, seed, versions and hashes). Reproduce them with `python src/models.py --table data/learning_table.csv --keys results/task2_validation_keys.csv --out-dir results`. The local prediction files are `model_validation_predictions.csv` and `model_none_predictions.csv`; they are named so they never overwrite the baseline `validation_predictions.csv`.

Task 4's SARIMA results on the 67-port high-activity subset are in `extension_run.json`, `extension_port_fits.csv` and `extension_subset_comparison.csv`; the decision is in `docs/extension_decision.md`. Its local prediction files are `extension_predictions.csv` and `extension_none_predictions.csv`.

Prediction CSVs, validation-key CSVs, row-level exclusion CSVs and `zero_runs.csv` are ignored. Compact audit/metric tables, reports and figures can be staged with `git add -A`; review them before committing. The Task 1 audit outputs require its original source metadata; the Task 2 runner uses the reviewed panel directly.

The diagnostic prediction file extends the protocol columns with `policy` and `clipping`; its unique key is `(policy,model,clipping,port_id,origin_date)`. Include these fields when aligning variants. All rows have split=validation. Active20 predictions are exported only on its common eligible cohort. Do not combine rows across policies or sum overlapping seven-day labels as distinct trade volumes. Shared production prediction files for later tasks retain the protocol's schema.

Suggested metric columns: model, feature_set, split, group_type, group_value, n_rows, n_ports, MAE, RMSE, WAPE_pct. Use NA for undefined WAPE. State units and sample counts on figures; export legible figures for the English paper and slides.

`baseline_review.json` preserves Hiếu's historical 10 November check. Final settings and freshly reproduced output hashes are in `task2_run.json`, `baseline_run.json` and `experiment.json`.
