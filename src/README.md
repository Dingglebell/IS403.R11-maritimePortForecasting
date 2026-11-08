# Workflow implementation

Task 1 cleaning and a separate audit/zero-policy diagnostic are implemented. Production features and model suites for the later tasks remain planned. The diagnostic is deliberately scoped to validation and does not score test or claim completion of Task 2.

| File | Owner | Input → output |
|---|---|---|
| prepare_data.py | Hân | Local snapshot → data/ports_daily.csv |
| analyze_task1.py | Hân | Snapshot + clean panel + experiment.json → dictionary-supporting audit, port metadata/lists, zero-policy validation and figures |
| features.py | Định, Hiếu | Daily panel + experiment.json → learning_table.csv |
| baselines.py | Định, Hiếu | Learning table → naïve and regression predictions |
| models.py | Huy, Tiến | Same learning table → RF/HGB predictions and settings |
| evaluate.py | Hân, Định, Hiếu | Aligned forecasts → metrics and figures |
| sarimax.py | Huy, Tiến | Optional; only after the feasibility decision |

Use functions for reading data, building features, fitting and exporting. Each script should accept explicit paths and configuration, avoid machine-specific absolute paths, and run from the repository root. Add exact commands to README only after they work.

Suggested environment: Python with pandas, NumPy, scikit-learn, Matplotlib and optionally statsmodels; pyarrow only if using Parquet. Create requirements.txt with tested versions once implementation begins. Do not present an untested package list as a reproducibility lock.

Before handoff, check a hand-worked seven-day label, a missing-date case, port isolation and boundary leakage. Verify the metrics against a tiny known example and WAPE’s zero-denominator case. Document checks beside each pull request.
