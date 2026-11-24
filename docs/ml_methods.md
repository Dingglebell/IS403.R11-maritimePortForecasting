# Random Forest and Histogram Gradient Boosting: methods and validation results

Status: validation only. The test split was not read and no model was refitted after validation (`refit_before_test: false`). All numbers below come from `results/model_validation_metrics.csv` and `results/model_candidates.csv`.

## Setup

- **Data:** the frozen Task 2 learning table (`data/learning_table.csv`, SHA256 `d54d3cbe…`). Training rows: 453,180. Validation rows: 75,390 across 210 ports. Observed zeros are retained. The validation keys match `results/task2_validation_keys.csv` exactly (SHA256 `97845d7f…`).
- **Target:** original total cargo (tonnes) over the next seven calendar days, `target_7d`.
- **Pooled samples:** one model per feature set, fitted on all ports together, as in the regression baselines.
- **Feature sets** (identical evaluation rows for each): `cargo_only` = cargo_7d; `cargo_calls` = cargo_7d + calls_7d; `cargo_mean28` = cargo_7d + cargo_mean_28d; `all_three` = all three.
- **Prediction rule:** `max(raw prediction, 0)` for every model, as agreed in Task 2. Nonnegative predictions are in `model_validation_predictions.csv`; raw predictions are kept in `model_none_predictions.csv` as a sensitivity. Both files are local and use the protocol schema. The names avoid overwriting the Task 2 baseline file `validation_predictions.csv`.
- **Selection:** for each model and feature set, the candidate with the lowest validation MAE of the nonnegative predictions. RMSE and WAPE are recorded. Seed 42, scikit-learn 1.9.1. The first run used Python 3.13.18; a rerun on Python 3.12 reproduced every candidate's metrics exactly. `model_config.json` records the environment of the committed run.

## Models and grids

| Model | Fixed | Grid (candidates per feature set) |
|---|---|---|
| Random Forest | squared-error split, `max_features=1.0`, bootstrap | trees {50, 100} × depth {6, 8, 14} × min leaf {50, 100, 300} = 18 |
| Histogram Gradient Boosting | `early_stopping=False` | loss {squared, absolute} × learning rate {0.05, 0.1} × iterations {100, 300} × max leaves {15, 63} × min leaf {20, 1000} = 32 |

HGB early stopping is disabled because scikit-learn's automatic holdout is a random split of time-ordered, overlapping seven-day windows and would leak. The iteration count is instead chosen on the chronological validation split.

The grids were widened once after a first run (RF depth {8, 14} × leaf {20, 100}; HGB squared loss only) because the best RF setting sat on the grid edge and HGB with squared loss performed poorly. That first run chose settings on the same validation rows, so the final grid reflects two rounds of validation tuning. Every candidate of the final run is recorded.

## Validation results (MAE in tonnes per seven-day target, nonnegative rule)

| Feature set | Random Forest | HGB | Seasonal naïve | Multivariate OLS |
|---|---:|---:|---:|---:|
| cargo_only | 54,809 | 55,390 | 51,628 | n/a (univariate OLS: 51,927) |
| cargo_calls | 53,140 | 52,488 | 51,628 | n/a |
| cargo_mean28 | 44,270 | 44,397 | 51,628 | n/a |
| all_three | **43,930** | 44,024 | 51,628 | **41,101** |

RMSE and WAPE for all variants are in `model_validation_metrics.csv`; WAPE is 18.95% (RF) and 18.99% (HGB) for `all_three`, against 17.73% for multivariate OLS and 22.27% for seasonal naïve.

Chosen settings (all in `model_config.json`): RF uses 50 trees and depth 8 (min leaf 50 for three feature sets, 100 for `cargo_mean28`). HGB uses absolute-error loss for every feature set.

## Interpretation

1. **Beating naïve depends on the 28-day mean.** With `cargo_only` or `cargo_calls`, both tree models are worse than seasonal naïve. With `cargo_mean28` or `all_three` they beat it by about 14–15%.
2. **Port calls add little.** Adding `calls_7d` improves `cargo_only` by 1,700–2,900 tonnes but adds only about 0.8% once `cargo_mean_28d` is present.
3. **Neither tree model beats multivariate OLS** (41,101). The best tree model (RF, `all_three`) is 6.9% worse. This is not evidence that trees are poor in general: the validation year has higher cargo than training (mean target 231,841 vs 206,403 tonnes; for example `port1201` averages about 10% more in validation). Trees predict averages of training leaves and cannot extrapolate beyond the levels seen in training, whereas a linear model scales with the input. We did not run a test of this explanation; it is a plausible reading of these descriptive statistics.
4. **Errors are concentrated.** With the chosen `all_three` settings, `port1201` alone accounts for 13.8% of HGB's and 13.3% of RF's total absolute error; no other port exceeds 3.5%. Pooled MAE is therefore dominated by a few very large ports. Every tree variant also has a negative mean bias (it under-forecasts on average), which is consistent with point 3. Task 5 should report per-port and per-group results.
5. **Squared-error HGB is fragile here.** The best squared-loss candidate for `all_three` gives MAE 55,754 and RMSE 235,542; absolute-error loss gives 44,024 and 130,879. Because the selection metric is MAE, the absolute-error loss is better aligned with it.

## Limitations

- Settings were chosen on validation, so tree validation scores are slightly optimistic compared with the untuned OLS baselines. Differences of well under 1% between candidates, and between RF and HGB on `all_three`, should not be treated as meaningful.
- Several chosen settings sit on a grid boundary (RF min leaf 50, HGB 63 leaves and 300 iterations for some feature sets). Wider grids might move scores slightly; the candidate table shows a flat region near the optimum.
- Daily seven-day targets overlap, so rows are dependent; results are descriptive for one validation year. No uncertainty interval is reported here.
- A validation improvement is not a test conclusion. Test scoring is for the frozen comparison in Task 5.

## Reproduce

```bash
python -m pip install -r requirements.txt
python src/models.py --table data/learning_table.csv --keys results/task2_validation_keys.csv --out-dir results
```

The full tuning run takes about 18 minutes on 2 CPU cores.
