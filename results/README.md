# Experiment outputs

Task 1 audit and controlled validation results exist here. Start with `data_audit.md` and `zero_validation.md`; interpretation is in `docs/zero_handling.md`. `zero_policy_metrics.csv` includes overall, target, country, activity, port and seven weekly-phase results. `paired_block_sensitivity.csv` records paired date-block estimates. `task1_run.json` is the single compact machine-readable record of hashes, versions and coefficients. Figures are in `figures/`. No test scores exist.

Task 2's four-baseline validation comparison is in `baseline_validation.md` and `baseline_metrics.csv`. Split boundaries/counts are in `task2_split_summary.csv`; provenance and code/table/key hashes are in `task2_run.json`. Reproduce these with `python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv`. Large learning, prediction and exclusion files stay local. The final working output uses the common nonnegative rule; the raw sensitivity is also reported.

Step 2's independent feature/split review is in `task2_feature_review.md`. `task2_feature_checks.csv` records the full-table comparisons; `task2_handcheck_summary.csv` and `task2_boundary_examples.csv` provide concrete review examples. Reproduce them with `python src/features.py --panel data/da_xu_ly/ports_daily.csv` followed by `python src/check_features.py`. The combined completion review is recorded in `docs/task2_completion.md`.

Prediction CSVs, validation-key CSVs, row-level exclusion CSVs and `zero_runs.csv` are ignored. Compact audit/metric tables, reports and figures can be staged with `git add -A`; review them before committing. The Task 1 audit outputs require its original source metadata; the Task 2 runner uses the reviewed panel directly.

The diagnostic prediction file extends the protocol columns with `policy` and `clipping`; its unique key is `(policy,model,clipping,port_id,origin_date)`. Include these fields when aligning variants. All rows have split=validation. Active20 predictions are exported only on its common eligible cohort. Do not combine rows across policies or sum overlapping seven-day labels as distinct trade volumes. Shared production prediction files for later tasks retain the protocol's schema.

Suggested metric columns: model, feature_set, split, group_type, group_value, n_rows, n_ports, MAE, RMSE, WAPE_pct. Use NA for undefined WAPE. State units and sample counts on figures; export legible figures for the English paper and slides.

`baseline_review.json` preserves Hiếu's historical 10 November check. Final settings and freshly reproduced output hashes are in `task2_run.json`, `baseline_run.json` and `experiment.json`.

## Task 5 evaluation

Start with the frozen Task 2 learning table and nonnegative validation forecasts. `src/evaluate.py` checks each model and feature set against the same reference rows. If a key, actual, country or target window differs, or a forecast is missing, duplicated or invalid, the evaluator reports the affected counts and stops before scoring.

Run against baselines and, once available locally, the Task 3 tree forecasts:

```bash
python src/evaluate.py --forecasts results/validation_predictions.csv results/model_validation_predictions.csv
```

The baseline file comes from `src/run_task2.py` and the tree file comes from `src/models.py` on the model handoff branch. To check the baseline export alone, pass only its file. For the optional SARIMA comparison, pass `results/extension_predictions.csv` as a third file and add `--activity-group high`. That scopes every model to the training-defined high-activity ports and requires complete coverage within the subset.

The command writes `metrics.csv`, `coverage.csv`, `highest_error_predictions.csv` and `evaluation_run.json` under `results/task5_validation/all_eligible/` or `results/task5_validation/high/`. These folders stay local. Set `--out-dir` to use a different writable folder. Metrics include pooled and mean-per-port MAE, RMSE, WAPE and bias. Country, activity, port and zero/positive-actual results use the same aligned rows. A blank WAPE means total actual cargo was zero. Weekly phases reuse every seventh origin, with phase 0 anchored at the first permitted origin for the split.

The first validation run used four baselines and eight selected tree variants from model commit `3670f89`. It matched 75,390 validation rows per variant over all 210 ports and 24,053 per variant over the 67-port high-activity subset. Multivariate regression had the lowest pooled MAE in both scopes.

Định reviews coverage, metric calculations and the scope of comparisons. Hiếu can use the validated forecasts and largest-error rows to prepare plots. Hân can use the country and activity rows to explain where planning decisions may differ by port. Estimated cargo can inform staffing, equipment and yard planning. Capacity or savings estimates require local productivity and capacity inputs.

Use this validation run to check the workflow. Before the shared 2026 test run, record the reviewed model commit, selected settings, cohort, forecast rule and evaluation scope. The evaluator can score a separately prepared test reference and forecasts with `--split test`. The current learning table contains training and validation rows.
