# Task 2 Step 2 feature and split review

The implementation and independent checks are complete. Hiếu's peer review is pending; the shared cohort/clipping decision remains Step 4.

Panel SHA256: `f8c402ed90ad70d851b0cf82e4c57d1d810cc3faa3bac958efd4bf68dd96d9b6`.
Learning-table SHA256: `d54d3cbe252556c79f10a17cb376b376b9918f72c546d0980471c1ef16f58c5a`.
Validation-key SHA256: `97845d7f3713f4c817859d0d4829aa366e6fbdf776e9c1f8716883ff271ccc38` (matches Task 1).
Checker SHA256: `697107c137cf7db70f979c7cf0efaf94a075c5214b72d48c8360311d8732305d`.

## Independent checks

All 528,570 learning rows match a separate cumulative-sum reconstruction of the three features and seven-day target (absolute tolerance 1e-8). Keys, country, activity group, target dates and split assignments match exactly.
Training-only eligibility, activity bands and the 20% candidate flag match for all 210 ports. All 8,400 excluded rows match by key and reason. Observed zeros remain in the source and target windows.

Training origins: 2019-01-28 through 2024-12-24; validation origins: 2024-12-31 through 2025-12-24.
Observations after the validation cutoff are removed before checking feature and label windows. No test targets or scores are generated.

## Direct calendar hand check

Port `port434`, origin 2024-12-31, split `validation`.

| Quantity | Calendar days | Direct calculation |
|---|---|---:|
| Cargo 7 days | 2024-12-25 to 2024-12-31 | 332,293 tonnes |
| Calls 7 days | Same seven dates | 148 calls |
| Cargo mean 28 days | 2024-12-04 to 2024-12-31 | 1,373,257 / 28 = 49,044.892857 tonnes/day |
| Target 7 days | 2025-01-01 to 2025-01-07 | 365,344 tonnes |

The 35 daily input rows and inclusion flags are exported locally to `data/task2_handcheck_daily.csv` by default. The compact summary and boundary examples are committed; daily source rows remain local.

## Exclusions

| Reason | Rows |
|---|---:|
| incomplete_history | 5,670 |
| target_beyond_validation | 1,470 |
| target_crosses_train_boundary | 1,260 |

The first 27 origins per port lack a full 28-day history. Origins 2024-12-25 through 2024-12-30 cross the training target boundary. Origins 2025-12-25 through 2025-12-31 need targets beyond validation and are excluded from this step.

## Hiếu review checklist

1. Sum the flagged dates in the local hand-check CSV and compare the four values above.
2. Inspect `task2_boundary_examples.csv`, especially 24/25/31 December 2024 and 24/25 December 2025.
3. Confirm the validation-key hash is unchanged from Task 1 and review the cohort proposal before Step 3/4.
