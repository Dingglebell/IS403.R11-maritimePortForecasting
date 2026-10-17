# Shared experiment protocol

This is the proposed implementation contract for Tasks 1–5. Confirm calendar cutoffs after inspecting the snapshot, then record them in `experiment.json`. Never choose cutoffs, ports, features or model settings because they improve test results.

## Forecast target and timing

For port p, daily cargo V(p,t) = import(p,t) + export(p,t), in estimated tonnes. At origin t, predict y(p,t) = sum of V(p,t+1) through V(p,t+7). This is one total per port and origin, not seven independent target outputs.

The experiment assumes observations through day t are available when the forecast is issued. Verify PortWatch publication delays and revisions; if the assumption fails, lag the information cutoff and adjust features. Historical revised data may give a more optimistic backtest than real-time operation; state this limitation.

## Daily panel and missingness

Standard columns: `date,port_id,country_iso3,import_tonnes,export_tonnes,portcalls,cargo_tonnes`. Retain source names in the dictionary. Enforce unique `(port_id,date)`, ascending daily dates and consistent units. A zero is an observed value; an absent or unknown observation is missing. Never silently fill missing dates or measurements with zero. Reindex each port onto a calendar before rolling calculations.

Select ports and define low/medium/high activity groups from training observations only. Candidate: at least 20% of training days with positive cargo; compare justified alternatives on validation. Record the denominator, coverage and country retention. Do not reuse the full-sample count of 138 ports as a train-only result.

Primary analysis requires complete feature and target windows. Document excluded rows. If imputation is needed, fit its rules on training data, use only past information, and compare on an unchanged evaluation set.

## Features and baseline definitions

| Name | Dates included | Unit |
|---|---|---|
| cargo_7d | Sum V from t-6 through t | tonnes |
| calls_7d | Sum portcalls from t-6 through t | calls |
| cargo_mean_28d | Mean V from t-27 through t | tonnes/day |
| target_7d | Sum V from t+1 through t+7 | tonnes |

Seasonal naïve predicts `cargo_7d`. Univariate linear regression uses `cargo_7d`; multivariate uses all three features; degree-2 regression uses `cargo_7d` and its square. RF and HGB use the same base features. Keep port identifiers for alignment; adding identifiers or calendar features is a separate documented experiment.

Proposed default: pool training rows across the selected ports for regression/RF/HGB and forecast each port-origin row. Optional SARIMA/SARIMAX is fitted per port. State the distinction in the paper.

## Chronological splits and label boundaries

Let A be the last training observation date and B the last validation observation date. Use common calendar boundaries across ports, not random row splits. Keep samples only when the entire target lies in its assigned period:

- Training: `t + 7 days <= A`.
- Validation: `t >= A` and `t + 7 days <= B`.
- Test: `t >= B` and `t + 7 days <= last observed date`.

This drops origins whose label windows cross the boundaries. Example: if A is 30 June, training origins end 23 June; 24–29 June are excluded; origin 30 June belongs to validation and predicts 1–7 July. Past feature history may cross a split boundary because it was available at the origin.

Fit all preprocessing on training data. Tune on validation MAE, using RMSE and WAPE as secondary checks. Use the same validation rows for every model and feature set. For HGB, avoid an automatic random early-stopping holdout; use fixed iterations selected on chronological validation or an explicit time-aware procedure.

For the simplest reproducible comparison, freeze the selected models trained on the training period and score test once. A later train-plus-validation refit is optional only if applied consistently and recorded before opening test results. During test, features can use observed history available up to each origin; no future targets enter model selection.

## Feature comparisons

Compare four sets for RF/HGB: cargo only; cargo plus calls; cargo plus 28-day mean; all three. Keep the rows fixed so missing windows do not change the comparison. Record seed, configuration, library versions, runtime and whether predictions were clipped at zero. Decide the clipping rule on validation and use it consistently.

## Output and evaluation

Prediction CSV columns: `model,feature_set,split,port_id,country_iso3,origin_date,target_start,target_end,y_true,y_pred`. Dates use YYYY-MM-DD. Unique key: `(model,feature_set,split,port_id,origin_date)`. `target_start = origin_date + 1 day`; `target_end = origin_date + 7 days`.

- MAE = mean absolute prediction error, in tonnes.
- RMSE = square root of mean squared prediction error, in tonnes.
- WAPE = 100 × sum absolute errors / sum actual tonnes. When the denominator is zero, report NA, not zero.

Report pooled metrics, country and training-defined activity groups, per-port metrics and macro-average port MAE. Report sample counts, failures and zero-actual windows. Calculate group WAPE from group sums, not an average of row percentages. Align identical keys before comparing models. Use a common subset for optional extensions and label it clearly.

Daily seven-day targets overlap. Treat observations as dependent, do not sum forecasts across origins as separate weekly volumes, and do not make independence-based significance claims. An every-seventh-origin sensitivity check can show how conclusions change.

## Optional oil extension and application limits

Huy/Tiến document a feasibility decision before implementation. Monthly oil values are available only after their publication date; never map a completed month’s value backward onto earlier days. SARIMAX needs an exogenous path for its horizon: use values actually known, forecasts or explicit scenarios. Compare against SARIMA and core models on the same ports and origins.

PortWatch provides estimated cargo activity, not measured terminal capacity. Forecasts can inform staffing, equipment and yard planning. Claims about utilisation, congestion or savings require independent capacity and productivity evidence. TEU and tonnes are different units and are not interchangeable.
