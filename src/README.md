# Planned implementation

Task 1 preparation is implemented in `prepare_data.py`; public acquisition is in `download_portwatch.py`. `validate_port_rules.py` is a validation-only eligibility sensitivity for joint review, with checks in `test_validate_port_rules.py`. It exercises the protocol's fixed linear/naive diagnostics without creating Task 2's production learning table or claiming its baseline work is complete. Keep the workflow simple and add the remaining files as their owners complete them.

`verify_task1.py` runs both test files and records the verification receipt only when every check passes with no skips. Run preparation, validation and then verification as documented in the root README.

| File | Owner | Input → output |
|---|---|---|
| prepare_data.py | Hân | Local snapshot → data/ports_daily.csv and audit |
| validate_port_rules.py | Hân, for joint Task 2 review | Audited panel + agreed dates → eligibility sensitivity on common validation keys |
| features.py | Định, Hiếu | Daily panel + experiment.json → learning_table.csv |
| baselines.py | Định, Hiếu | Learning table → naïve and regression predictions |
| models.py | Huy, Tiến | Same learning table → RF/HGB predictions and settings |
| evaluate.py | Hân, Định, Hiếu | Aligned forecasts → metrics and figures |
| sarimax.py | Huy, Tiến | Optional; only after the feasibility decision |

Task 1 supports an audit-only default and an opt-in training-only candidate selection step. See the root README for exercised commands and `docs/task1_handoff.md` for agreement and review status. The standalone sensitivity constructs protocol windows in memory from pre-test data only; test rows are removed first. It records all common validation keys, per-rule training exclusions, training-fitted regression scaling, predictions and metrics for reproduction. It does not generate `learning_table.csv`, implement Task 2's full baseline comparison or score test.

Use functions for reading data, building features, fitting and exporting. Each script should accept explicit paths and configuration, avoid machine-specific absolute paths, and run from the repository root. Add exact commands to README only after they work.

Suggested environment: Python with pandas, NumPy, scikit-learn, Matplotlib and optionally statsmodels; pyarrow only if using Parquet. Create requirements.txt with tested versions once implementation begins. Do not present an untested package list as a reproducibility lock.

Before handoff, check a hand-worked seven-day label, a missing-date case, port isolation and boundary leakage. Verify the metrics against a tiny known example and WAPE’s zero-denominator case. Document checks beside each pull request.
