# Task 2 Features and baseline models

**Owners:** Phạm Công Định, Lê Nguyễn Hữu Hiếu

**Stage:** 3 | **Handoff deadline:** 8 November 2026

Create one reproducible learning table and establish the baseline comparisons.

## Inputs

Task 1 clean panel, data dictionary and port-selection rules. Use docs/protocol.md as the shared contract.

## Work

1. Suggested split: Định builds features and split checks; Hiếu builds baselines and prediction exports. Each reviews the other’s work.
2. At origin t, use cargo and calls from t-6 to t, plus mean daily cargo from t-27 to t. The label is total cargo from t+1 to t+7. Calculate within each port on a complete daily calendar.
3. Agree and record calendar cutoffs. Keep label windows wholly inside their assigned period. Fit preprocessing on training data only; never shuffle dates.
4. Run seasonal naïve, univariate linear regression, multivariate linear regression and degree-2 regression. Naïve equals the last seven-day cargo total; degree 2 uses cargo_7d and its square.
5. Check a hand-calculated example and boundary cases. Use the same port-origin rows for all models. Produce validation results first; reserve final test scoring for the frozen comparison.

## Deliverables

| File or location | Expected output |
|---|---|
| `src/features.py` | Feature creation and split checks |
| `src/baselines.py` | Four baseline models |
| `data/learning_table.csv` | Features, labels and split membership |
| `results/validation_predictions.csv` | Common prediction schema |
| `docs/features_baselines.md` | English method section |

## Completion check

Prove that inputs contain no future data and labels do not cross cutoffs. Hand off exact split dates, feature definitions and baseline validation results to Huy and Tiến. The stage-table target is 1 November; the assigned deadline is 8 November.

Suggested subroles and file paths are implementation proposals; owners and assignment deadlines follow the work plan. These are future deliverables, not files claimed to exist now.
