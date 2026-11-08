# Workflow implementation

Task 1 cleaning and its audit/zero-policy diagnostic are implemented. Task 2 now has shared features, four baselines and a one-command runner. Both stages score validation only; final cohort/clipping decisions and test evaluation remain pending.

| File | Owner | Input → output |
|---|---|---|
| prepare_data.py | Hân | Local snapshot → data/ports_daily.csv |
| analyze_task1.py | Hân | Snapshot + clean panel + experiment.json → dictionary-supporting audit, port metadata/lists, zero-policy validation and figures |
| features.py | Định, Hiếu | Daily panel + experiment.json → learning_table.csv |
| baselines.py | Định, Hiếu | Learning table → naïve and regression predictions |
| run_task2.py | Định, Hiếu | Verified Task 1 panel → features, four baselines, validation metrics and run record |
| models.py | Huy, Tiến | Same learning table → RF/HGB predictions and settings |
| evaluate.py | Hân, Định, Hiếu | Aligned forecasts → metrics and figures |
| sarimax.py | Huy, Tiến | Optional; only after the feasibility decision |

Use functions for reading data, building features, fitting and exporting. Each script should accept explicit paths and configuration, avoid machine-specific absolute paths, and run from the repository root. Add exact commands to README only after they work.

Task 1/2 use the pinned `requirements.txt`. Baseline regressions use NumPy ordinary least squares. RF/HGB will need scikit-learn and the optional SARIMAX branch may need statsmodels; add tested versions when those implementations begin.

Task 2 commands and role assignments are in `docs/task2_pipeline.md`. Use `python src/run_task2.py` from the root for the full verified workflow; `features.py` and `baselines.py` also run separately for development.

Before handoff, check a hand-worked seven-day label, a missing-date case, port isolation and boundary leakage. Verify the metrics against a tiny known example and WAPE’s zero-denominator case. Document checks beside each pull request.
