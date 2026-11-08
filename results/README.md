# Experiment outputs

Task 1 audit and controlled validation results exist here. Start with `data_audit.md` and `zero_validation.md`; interpretation is in `docs/zero_handling.md`. `zero_policy_metrics.csv` includes overall, target, country, activity, port and seven weekly-phase results. `paired_block_sensitivity.csv` records paired date-block estimates. `task1_run.json` is the single compact machine-readable record of hashes, versions and coefficients. Figures are in `figures/`. No test scores exist.

Task 2's four-baseline validation comparison is in `baseline_validation.md` and `baseline_metrics.csv`. Split boundaries/counts are in `task2_split_summary.csv`; provenance and code/table/key hashes are in `task2_run.json`. Reproduce these with `python src/run_task2.py`. Large learning, prediction and exclusion files stay local. The working output uses raw forecasts while final cohort/clipping agreement remains pending; the separate nonnegative variant is also reported.

Large raw/prediction/key/exclusion/run-level files remain local and ignored. Only reviewed small audit/metric tables, reports and figures are committed. Recreate all outputs with `python src/analyze_task1.py` after preparing the panel.

The diagnostic prediction file extends the protocol columns with `policy` and `clipping`; its unique key is `(policy,model,clipping,port_id,origin_date)`. Include these fields when aligning variants. All rows have split=validation. Active20 predictions are exported only on its common eligible cohort. Do not combine rows across policies or sum overlapping seven-day labels as distinct trade volumes. Shared production prediction files for later tasks retain the protocol's schema.

Suggested metric columns: model, feature_set, split, group_type, group_value, n_rows, n_ports, MAE, RMSE, WAPE_pct. Use NA for undefined WAPE. State units and sample counts on figures; export legible figures for the English paper and slides.
