# Task 3 Random Forest and Histogram Gradient Boosting

**Owners:** Trần Hoàng Huy, Lê Minh Tiến

**Stage:** 4 | **Handoff deadline:** 25 November 2026

Compare the two tree models fairly and test whether extra inputs improve forecasts.

## Inputs

Task 2 learning table, split dates, baseline results and prediction format.

## Work

1. Suggested split: Huy implements Random Forest; Tiến implements Histogram Gradient Boosting. Share one training and export interface, then review each other’s code.
2. Use the same pooled port-day samples as regression. Train each candidate only on training data and choose settings using validation MAE. Save the candidate grid, seed, runtime and chosen settings.
3. Compare cargo_7d alone; cargo_7d plus calls_7d; cargo_7d plus cargo_mean_28d; and all three. Keep the evaluation rows identical across feature sets.
4. For Random Forest, start with small grids for tree count, depth and leaf size. For boosting, try learning rate, iterations and leaf size. Disable automatic random early-stopping splits or supply an explicitly chronological validation procedure.
5. Choose any nonnegative prediction rule on validation and apply it consistently. Freeze the configuration before producing final test forecasts; coordinate final scoring with Task 5.

## Deliverables

| File or location | Expected output |
|---|---|
| `src/models.py` | Both models and tuning procedure |
| `results/model_config.json` | Grid, chosen settings, seed and versions |
| `results/validation_predictions.csv` | Validation predictions for each variant |
| `docs/ml_methods.md` | English methods and experiment setup |

## Completion check

Every model and feature comparison is reproducible on identical rows. Explain improvements or failures relative to naïve and regression. The stage-table target is 8 November; the assigned deadline is 25 November.

Suggested subroles and file paths are implementation proposals; owners and assignment deadlines follow the work plan. These are future deliverables, not files claimed to exist now.
