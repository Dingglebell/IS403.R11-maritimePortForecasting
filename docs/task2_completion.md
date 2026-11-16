# Task 2 completion and model handoff

Task 2 is complete as of 16 November 2026. The completion review integrates Định's feature/split evidence in PR 4 and Hiếu's baseline validation in PR 5. All 33 combined tests pass, the full run reproduces, and the final comparison rules are recorded in `experiment.json`. This is a completion decision under the project owner's request, not a claim of individual approvals by team members.

## Decisions for the shared comparison

| Item | Recorded rule |
|---|---|
| Target | Original estimated import plus export over t+1 through t+7, in tonnes |
| Cohort | All 210 IDs with complete training cargo and call coverage |
| Zero days | Retained as observations; unknown values remain missing |
| Features | Cargo sum and call sum over t−6…t; mean daily cargo over t−27…t |
| Training | 2019–2024; origins end 24 December 2024 |
| Validation | Targets entirely in 2025; origins 31 December 2024–24 December 2025 |
| Test | Reserved 2026-01-01–2026-10-02; not scored |
| Forecast rule | Bound every model's forecast below by zero; save raw forecasts as a sensitivity |
| Model fitting | Pooled ports, training-only fitting and preprocessing; no validation refit |
| Selection metric | Validation MAE; also report RMSE and WAPE |

Retaining the broader cohort follows Task 1's coverage analysis. The 20% activity candidate removes 73 ports for a 0.0268% MAE improvement on the common 137-port cohort; it remains a sensitivity, not the shared population. Nonnegative clipping is a domain constraint: for nonnegative actual cargo, replacing a negative forecast by zero cannot increase its absolute or squared error. Apply this same rule to RF/HGB and any optional model.

## Final baseline validation

All four models use the same 75,390 validation origins across 210 ports. Training has 453,180 complete rows. Metrics below use the common nonnegative rule.

| Baseline | MAE tonnes | RMSE tonnes | WAPE percent |
|---|---:|---:|---:|
| Seasonal naïve | 51,627.80 | 128,402.46 | 22.2687 |
| Univariate linear | 51,926.57 | 128,248.51 | 22.3975 |
| Multivariate linear | **41,100.62** | **101,217.66** | **17.7280** |
| Degree 2 | 52,369.56 | 128,114.94 | 22.5886 |

Multivariate linear regression improves validation MAE by about 20.39% relative to seasonal naïve. The other two regressions do not beat naïve on MAE. This ranks these baselines on validation only; it does not establish test performance or the benefit of each added feature separately. Raw multivariate forecasts include 14,846 negatives; both forecast variants and their scores remain available.

## Completion evidence

- Reviewed source hashes match Task 1. The 528,570-row learning table and validation-key hash are unchanged.
- Independent cumulative-sum reconstruction checks every feature/label and all 8,400 exclusions, plus training-only eligibility and activity groups.
- The 35-day Hải Phòng example matches the table: 332,293 prior-seven-day tonnes, 148 calls, 49,044.892857 tonnes/day over 28 days, and a 365,344-tonne next-seven-day target.
- The combined test suite includes Hiếu's standalone export/provenance tests and the independent Step 2 checks; all 33 pass.
- Final raw/nonnegative prediction files have identical keys and original labels. Metrics are independently recomputed from the exported forecasts.

`results/task2_run.json` records the final pipeline run; `results/baseline_run.json` records the final standalone baseline run and output hashes. `results/baseline_review.json` and `docs/task2_hieu_baseline_review.md` preserve Hiếu's earlier 10 November review and its then-pending decisions; they are historical evidence, not the final configuration.

## Handoff to Huy and Tiến

The final Task 3 readiness pass reproduces this workflow from a fresh source folder with only the frozen clean CSV supplied as local data. All 34 tests pass, including the feature-variant scoring regression. Follow [the Task 3 start guide](task3_start.md) for responsibilities, feature comparisons and export checks.

From the repository root, with Hân's clean panel and the pinned environment:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s src -p 'test_*.py' -v
python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv
python src/check_features.py
```

Use `data/learning_table.csv` for training and validation. It contains the shared features, original labels, split, country and activity group. Use the exact `(port_id, origin_date)` keys in `results/task2_validation_keys.csv`. The common baseline output is `results/validation_predictions.csv`; raw and nonnegative variants are also exported separately. Large local artifacts are shared through the group's existing channel or regenerated, rather than committed.

For Task 3, fit RF/HGB on the same training rows, choose settings on the same validation rows, apply the same nonnegative rule, and compare against these baselines. Run the cargo-only, cargo-plus-calls, cargo-plus-28-day-mean and all-three feature sets on identical keys. Disable a random automatic early-stopping split or use an explicit chronological validation procedure. Keep test evaluation for the later frozen comparison.

The English method section is `docs/features_baselines.md`. PortWatch data are estimated; historical publication vintages are unavailable. Same-day observation availability remains a retrospective assumption, and forecasts do not measure congestion, capacity or cost savings.
