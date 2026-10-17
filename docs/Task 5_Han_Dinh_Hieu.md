# Task 5 Evaluation and operational interpretation

**Owners:** Nguyễn Thị Quỳnh Hân, Phạm Công Định, Lê Nguyễn Hữu Hiếu

**Stage:** 5 | **Handoff deadline:** 15 December 2026

Produce the final comparison and explain what cargo forecasts can support in capacity planning.

## Inputs

Frozen configurations and predictions from Tasks 2 and 3; optional extension output; training-defined port groups from Task 1.

## Work

1. Suggested split: Định validates metrics and alignment; Hiếu prepares comparison plots; Hân analyses countries, activity groups and business implications. Review one another’s conclusions.
2. Assert one prediction per model, port and origin. Align identical rows and target windows before scoring. Report excluded or failed predictions and evaluated sample counts.
3. Report MAE and RMSE in tonnes and WAPE in percent, overall and by country and activity group. If total actual cargo is zero, WAPE is undefined; retain MAE and RMSE.
4. Show per-port results and macro-average MAE as well as pooled metrics so large ports do not hide small-port errors. Compare zero-actual and positive-actual windows separately.
5. Plot observed versus predicted totals and high-error cases. Explain that daily seven-day forecasts overlap; do not sum them as independent weekly cargo. Use an every-seventh-origin sensitivity check if time permits.
6. Connect higher expected cargo to staffing, equipment and yard planning. Quantitative capacity estimates need separate productivity or capacity inputs; do not claim measured congestion or proven cost savings.

## Deliverables

| File or location | Expected output |
|---|---|
| `src/evaluate.py` | Shared evaluation code |
| `results/test_predictions.csv` | Frozen aligned test forecasts |
| `results/metrics.csv` | Metrics, counts and group labels |
| `results/` | Comparison tables and figures |
| `docs/results_discussion.md` | English results and business implications |

## Completion check

Tables and charts are generated from saved forecasts, with no test-based retuning. State limitations and whether each model beats naïve. The stage-table target is 15 November; the assigned deadline is 15 December.

Suggested subroles and file paths are implementation proposals; owners and assignment deadlines follow the work plan. These are future deliverables, not files claimed to exist now.
