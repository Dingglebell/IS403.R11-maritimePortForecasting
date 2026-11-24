# Workflow implementation

Task 1 covers cleaning and data audit. Task 2 builds the shared features and compares four baselines on validation. Task 5 uses the frozen 210-port cohort and forecast rule for the 2026 test run.

| File | Owner | Status and purpose |
|---|---|---|
| prepare_data.py | Hân | Implemented: raw CSVs → clean daily panel |
| analyze_task1.py | Hân | Implemented: source metadata + panel → audit, port lists and zero-policy validation |
| features.py | Định, Hiếu | Implemented: panel + experiment.json → common learning table |
| check_features.py | Định, Hiếu | Implemented: independent full-table calculation, hand check and boundary review |
| baselines.py | Định, Hiếu | Implemented: learning table → four baseline predictions and metrics |
| run_task2.py | Định, Hiếu | Implemented: verified clean panel → complete Task 2 validation run |
| models.py | Huy, Tiến | Planned: RF/HGB predictions and settings |
| evaluate.py | Định | Implemented: forecast alignment, coverage checks and evaluation tables |
| run_task5_test.py | Định | Implemented: fixed model settings and aligned 2026 test results |
| sarimax.py | Huy, Tiến | Optional, not implemented |

Use functions for reading data, building features, fitting and exporting. Each script should accept explicit paths and configuration, avoid machine-specific absolute paths, and run from the repository root. Add exact commands to README only after they work.

Task 1/2 use the pinned `requirements.txt`. Baseline regressions use NumPy ordinary least squares. RF/HGB will need scikit-learn and the optional SARIMAX branch may need statsmodels; add tested versions when those implementations begin.

Task 2 commands and role assignments are in `docs/task2_pipeline.md`. From the repository root, use `python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv` with Hân's current handoff. `features.py` and `baselines.py` also run separately for development.

Task 3 starts with `docs/task3_start.md`. The validation metric helper in `baselines.py` scores each `(model, feature_set)` separately; pass one clipping variant at a time.

`run_task5_test.py` recreates the frozen Task 5 test forecasts with the reviewed Task 2 learning table and Task 3 model handoff. See the Task 5 commands in `results/README.md`.

Before handoff, check a hand-worked seven-day label, a missing-date case, port isolation and boundary leakage. Verify the metrics against a tiny known example and WAPE’s zero-denominator case. Document checks beside each pull request.
