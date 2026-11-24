# Experiment outputs

Task 1 audit and controlled validation results exist here. Start with `data_audit.md` and `zero_validation.md`. Interpretation is in `docs/zero_handling.md`. `zero_policy_metrics.csv` includes overall, target, country, activity, port and seven weekly-phase results. `paired_block_sensitivity.csv` records paired date-block estimates. `task1_run.json` records hashes, versions and coefficients. Figures are in `figures/`.

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

The validation run checked the evaluation workflow before the 2026 test. The learning table still contains training and validation rows. `run_task5_test.py` prepares the test reference and passes the resulting forecasts to the same evaluator.

### Fixed 2026 test results

Định's evaluation used each configuration fixed before test scoring in `task5_freeze.json`. Each of the 12 variants covered 56,490 port-origin rows across 210 ports, with zero exclusions, missing forecasts or duplicate keys. Test target dates run from 1 January to 2 October 2026. The primary table uses the four baselines and the three-input version of each tree model selected on 2025 validation MAE.

| Model | MAE (tonnes) | RMSE (tonnes) | WAPE (%) | MAE change vs naïve (%) |
|---|---:|---:|---:|---:|
| Multivariate linear regression | 41,760.63 | 109,449.89 | 18.20 | −19.27 |
| Random Forest | 44,210.86 | 130,533.72 | 19.27 | −14.53 |
| Histogram Gradient Boosting | 44,403.01 | 140,827.35 | 19.35 | −14.16 |
| Seasonal naïve | 51,726.09 | 129,106.54 | 22.54 | 0.00 |
| Univariate linear regression | 51,951.97 | 128,777.22 | 22.64 | +0.44 |
| Degree-2 regression | 52,325.51 | 128,748.33 | 22.80 | +1.16 |

Multivariate regression had the lowest pooled MAE and RMSE. Both tree models improved MAE relative to seasonal naïve, while their higher RMSE highlights larger misses. Histogram Gradient Boosting had the lowest MAE among the primary models for the low- and medium-activity groups. Multivariate regression led the high-activity group and all seven non-overlapping origin phases. The pooled and macro-port MAE coincide because each port has 269 evaluated origins. Port metrics and group breakdowns show where the overall averages hide differences.

The model predicts a seven-day total at each daily forecast origin, so consecutive target windows overlap. Interpret the metrics as forecast errors across those windows. WAPE is the total absolute error as a percentage of the sum of actuals across evaluated windows. It is undefined in the zero-actual group, which contains 14,626 windows per variant. Compare MAE and RMSE there. PortWatch cargo is estimated, and the evaluation assumes observations through the origin are available at forecast time.

The [summary CSV](task5_test_summary.csv) contains the 12 overall comparisons and flags the primary rows. The [metrics CSV](metrics.csv) contains the country, activity, port, zero/positive-actual and phase breakdowns. The [coverage report](task5_test_coverage.csv) and [run record](task5_test_run.json) track alignment and checksums. The input features and labels were independently reconstructed for every test row, and overall scores were checked against the saved predictions. The suite has 40 passing tests.

Hiếu can use the run's local `test_predictions.csv` and `highest_error_predictions.csv` for the figures. Hân can use the metrics and coverage report for interpretation. Estimated cargo can support staffing, equipment and yard planning. Turning forecasts into staffing hours or utilization requires local productivity and capacity data.

### Reproduce the fixed test comparison

`task5_freeze.json` records the analysis plan before test scoring. The primary table compares six approaches on the same 210 ports. The six other forest or boosting feature sets appear as feature sensitivity rows. Task 4's SARIMA result stays with its 67-port validation analysis.

Use the frozen clean panel and Task 2 learning table. If you need the learning table, run `python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv`. In Git Bash, retrieve the exact reviewed Task 3 model source and settings and run the test comparison:

```bash
git fetch origin task3-4-models-extension
git archive --format=zip -o data/task34-handoff.zip 3670f89b97730b8eb12ae05050b12a0ce3d10b0e src/models.py results/model_config.json
python -m zipfile -e data/task34-handoff.zip data/task34-handoff
python -m pip install -r requirements.txt scikit-learn==1.9.1
python src/run_task5_test.py --model-handoff data/task34-handoff
```

The runner checks the file hashes and package versions in the freeze record. It fits the saved settings with the 2019–2024 training rows and uses observations through each origin for predictors. It scores the original cargo over the next seven days. It saves the forecasts, metrics, coverage, window exclusions and run hashes under `results/task5_test/`. Keep the row-level data local and use `--out-dir` with a new writable folder for a reproduction.
