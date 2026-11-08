# Workflow implementation

Task 1 cleaning and its audit/zero-policy diagnostic are implemented. Task 2 now has shared features, four baselines and a one-command runner. Both stages score validation only; final cohort/clipping decisions and test evaluation remain pending.

| File | Owner | Status and purpose |
|---|---|---|
| prepare_data.py | Hân | Implemented: raw CSVs → clean daily panel |
| analyze_task1.py | Hân | Implemented: source metadata + panel → audit, port lists and zero-policy validation |
| features.py | Định, Hiếu | Implemented: panel + experiment.json → common learning table |
| baselines.py | Định, Hiếu | Implemented: learning table → four baseline predictions and metrics |
| run_task2.py | Định, Hiếu | Implemented: verified clean panel → complete Task 2 validation run |
| models.py | Huy, Tiến | Planned: RF/HGB predictions and settings |
| evaluate.py | Hân, Định, Hiếu | Planned: final aligned comparison and figures |
| sarimax.py | Huy, Tiến | Optional, not implemented |

Use functions for reading data, building features, fitting and exporting. Each script should accept explicit paths and configuration, avoid machine-specific absolute paths, and run from the repository root. Add exact commands to README only after they work.

Task 1/2 use the pinned `requirements.txt`. Baseline regressions use NumPy ordinary least squares. RF/HGB will need scikit-learn and the optional SARIMAX branch may need statsmodels; add tested versions when those implementations begin.

Task 2 commands and role assignments are in `docs/task2_pipeline.md`. From the repository root, use `python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv` with Hân's current handoff. `features.py` and `baselines.py` also run separately for development.

Before handoff, check a hand-worked seven-day label, a missing-date case, port isolation and boundary leakage. Verify the metrics against a tiny known example and WAPE’s zero-denominator case. Document checks beside each pull request.
