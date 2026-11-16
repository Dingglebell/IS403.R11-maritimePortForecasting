# Task 3 start guide for Huy and Tiến

Task 2 is complete. Begin RF/HGB experiments from the latest `main`, using the final rules in `experiment.json` and the baseline evidence in [the completion handoff](task2_completion.md). Suggested split: Huy leads Random Forest and Tiến leads Histogram Gradient Boosting; each reviews the other's work.

## Reproduce the starting point

Obtain Hân's frozen `ports_daily.csv` through the group channel and place it at `data/da_xu_ly/ports_daily.csv`. The dataset is local, so cloning GitHub alone does not provide it. The full Task 1 source metadata file is not needed for this step.

From the repository root, install the pinned environment and run:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s src -p 'test_*.py' -v
python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv
python src/check_features.py
```

Expected: 210 ports, 453,180 training rows and 75,390 validation rows per model. The clean-panel hash must match Task 1. The learning-table SHA256 is `d54d3cbe252556c79f10a17cb376b376b9918f72c546d0980471c1ef16f58c5a`; the validation-key SHA256 is `97845d7f3713f4c817859d0d4829aa366e6fbdf776e9c1f8716883ff271ccc38`.

Use `data/learning_table.csv` and split it by its `split` column. Keep `port_id` and `origin_date` for alignment. `target_7d` is the original next-seven-day cargo total. The baseline prediction file is `results/validation_predictions.csv`. It uses nonnegative forecasts; raw baseline predictions remain in `results/baseline_none_predictions.csv`.

## Model experiments

Add a tested, pinned scikit-learn version to `requirements.txt` in the Task 3 PR; it is not needed for the existing NumPy baselines. Implement the tree models in `src/models.py` with explicit input/config/output arguments.

| Feature set | Inputs |
|---|---|
| cargo_only | cargo_7d |
| cargo_calls | cargo_7d, calls_7d |
| cargo_mean28 | cargo_7d, cargo_mean_28d |
| all_three | cargo_7d, calls_7d, cargo_mean_28d |

Fit on training rows only. Choose settings using validation MAE, record every candidate, the seed (42), chosen settings and runtime, and report RMSE/WAPE too. For HGB, disable an automatic random early-stopping holdout or implement an explicit chronological validation procedure. Every feature comparison must use the same port-origin rows.

Use all 210 eligible ports and retain observed zeros. Apply `max(raw_prediction, 0)` to every model for the common comparison; retain raw predictions as a sensitivity. Do not change the cohort, cutoffs, labels or preprocessing based on test performance. Test remains reserved for the later frozen comparison; the Task 2 learning table intentionally contains train/validation only.

## Export and handoff checks

Follow the columns in `docs/protocol.md`: `model,feature_set,split,port_id,country_iso3,origin_date,target_start,target_end,y_true,y_pred`. If exporting both clipping variants, use separate files or include `clipping` in the identifier.

- Each `(model, feature_set, port_id, origin_date)` key is unique within a validation/clipping variant.
- Each variant has exactly the 75,390 keys in `results/task2_validation_keys.csv`, with identical original labels.
- Compare each model and feature set separately. `score_predictions` in `src/baselines.py` can score validation forecasts with `model` and `feature_set` columns; its grouping keeps feature variants separate. Do not mix raw and nonnegative variants in one scoring call.
- The reference MAEs are 51,627.80 tonnes for seasonal naïve and 41,100.62 tonnes for multivariate regression. A validation improvement is not a test conclusion.
- Record versions, code/config/data hashes, tuning settings and row counts. Keep large prediction files local; commit code, compact comparisons and a concise English methods update.

Use task branches and pull requests following [the Git guide](git_bash_guide.md). The original Task 3 assignment remains [Task 3 Huy Tien](Task%203_Huy_Tien.md).
