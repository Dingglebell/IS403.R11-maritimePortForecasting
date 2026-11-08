# Task 2 pipeline for Định and Hiếu

Turn Hân's clean daily panel into one shared learning table, then compare seasonal naïve and three regressions on identical validation rows. The code is ready to run. Port selection and clipping remain proposals until you both agree; this pipeline does not freeze them or score test.

## Workflow and responsibilities

| Step | Lead | Work and review |
|---|---|---|
| 1 Receive the handoff | Both | Check Task 1 provenance, dates and the recommended 210-port cohort. Confirm observed zeros remain unchanged. |
| 2 Create features and splits | Định | Review `src/features.py`, hand-check one port/date and inspect excluded boundary rows. Hiếu reviews the checks. |
| 3 Fit four baselines | Hiếu | Review `src/baselines.py`, inspect predictions and compare raw versus nonnegative results. Định reviews training-only fitting. |
| 4 Agree the shared rules | Both | Decide the common cohort and clipping rule from validation, record the agreement in `experiment.json`, and rerun. |
| 5 Hand off to Huy and Tiến | Both | Share the exact snapshot, learning table, validation keys, metrics and model definitions through a pull request and the group's data-sharing channel. |

Pipeline: clean daily panel → training-only port rules → calendar features and labels → chronological train/validation rows → four baselines → predictions and MAE/RMSE/WAPE.

## Run from the repository root

Install the pinned environment once:

```bash
python -m pip install -r requirements.txt
```

Hân's supplied folders are `data/chua_xu_ly/` for raw CSVs and `data/da_xu_ly/` for processed data. The supplied `data/da_xu_ly/ports_daily.csv` and all ten raw CSVs match the reviewed Task 1 hashes. Use the processed CSV directly; the Excel copy is not needed by the pipeline.

If you need to rebuild a canonical clean panel from the raw files:

```bash
python src/prepare_data.py --input-dir data/chua_xu_ly --output data/ports_daily.csv
```

The one-command runner verifies that the clean panel's hash matches Task 1's reviewed record; revised downloads require a separate audit. To run directly from Hân's supplied processed folder:

```bash
python -m unittest discover -s src -p 'test_*.py' -v
python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv
```

To work separately, Định can export the table and Hiếu can run baselines from it:

```bash
python src/features.py --panel data/da_xu_ly/ports_daily.csv
python src/baselines.py
```

The combined command adds snapshot verification and a run record. Both commands use the same functions. The lower-level commands support development and do not independently verify the source snapshot hash.

## Definitions to check together

At origin t, features use observations through t only: cargo sum over t−6…t, calls sum over t−6…t and mean daily cargo over t−27…t. The label is the original cargo sum over t+1…t+7. All windows are computed separately per port on a daily calendar. Missing measurements exclude the affected windows; genuine zeros stay.

Training observations cover 2019–2024. Training origins end 24 December 2024 so all labels end within training. Validation origins run from 31 December 2024 through 24 December 2025, with target windows wholly in 2025. The pipeline removes 2026 observations before feature, label and port-selection calculations. Histories for later validation origins can use observations available by that origin; models remain fitted on training only.

All four models share the same complete rows, including the 28-day history requirement even for naïve. The default cohort is Hân's complete-training-cargo-and-calls recommendation, with the 20% candidate flag retained for review. No full-snapshot activity statistic sets eligibility.

| Model | Inputs and rule |
|---|---|
| Seasonal naïve | Forecast equals `cargo_7d` |
| Univariate linear | Intercept plus `cargo_7d` |
| Multivariate linear | Intercept plus all three features |
| Degree 2 | Intercept, `cargo_7d` and its square |

Regressions use NumPy ordinary least squares; no new modelling dependency is needed. Scaling is fitted on training rows only. For numerical stability, the quadratic model squares training-standardized cargo; this spans the same degree-2 polynomial as raw cargo and raw cargo squared.

## Files to inspect

| Output | What to check |
|---|---|
| `data/learning_table.csv` | Keys, feature values, original targets and split membership |
| `results/task2_split_summary.csv` | Date boundaries, row counts and port counts |
| `results/task2_ports.csv` | Training coverage, activity bands and candidate 20% flag |
| `results/task2_exclusion_summary.csv` | Reasons for dropping incomplete or boundary windows |
| `results/task2_window_exclusions.csv` | Exact excluded port-origin rows |
| `results/validation_predictions.csv` | One forecast per model, port and validation origin |
| `results/baseline_none_predictions.csv` | Unclipped predictions |
| `results/baseline_nonnegative_predictions.csv` | The same predictions bounded below by zero |
| `results/baseline_metrics.csv` | Four models under each clipping variant, sample counts and errors |
| `results/baseline_validation.md` | Readable validation comparison |
| `results/baseline_fits.json` | Training scales, coefficients and model rank |
| `results/task2_run.json` | Snapshot, config/code/table/key hashes and run settings |

MAE and RMSE are tonnes per seven-day target. WAPE is `100 × total absolute error / total actual cargo`; it is blank if the denominator is zero. Overlapping seven-day labels are dependent; these are descriptive validation comparisons.

While `clip_negative_predictions` is null, the working prediction file contains raw forecasts and both variants are reported for discussion. This is a temporary output convention, not agreement on the final rule. Set the shared field to `true` or `false` after joint review. An explicit `--clipping none` or `--clipping nonnegative` overrides the output variant for that run and is recorded in the run record. Do not choose a different clipping variant per model without documenting a new design.

The verified first run contains 453,180 training rows and 75,390 validation rows per model across 210 ports. Its learning rows match Task 1's calendar windows, and its validation-key hash is identical. See `results/baseline_validation.md` for the provisional comparison. All 27 repository tests pass.

## Completion and pull request

Định signs off the calendar examples, split boundaries and training-only eligibility. Hiếu signs off all four model definitions, equal evaluation keys and the error calculations. Both review the English methods draft in `docs/features_baselines.md` and record the shared rule decision before final test work.

Raw data, the learning table and large prediction/exclusion files remain local under the repository's ignore rules. Publish only code, documentation and reviewed compact summaries. Share the frozen local artifacts with Huy/Tiến through the agreed group channel. Run `git add -A`, commit, push your task branch, and open a pull request into `main` following the Git guide.
