# Zero-policy validation (generated)

No test scores. Joint review pending. Methods and interpretation: `docs/zero_handling.md`.

## Primary scores

| policy | model | clipping | cohort | group_type | group | n | ports | MAE | RMSE | WAPE_pct | macro_port_MAE | bias | zero_actual_windows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active20 | OLS | nonnegative | common_active20 | overall | all | 49183 | 137 | 58,943.5435 | 124,399.3270 | 16.7908 | 58,943.5435 | 272.5683 | 1827 |
| always_zero | zero_reference | not_applicable | all_eligible | overall | all | 75390 | 210 | 231,840.5442 | 1,196,221.2554 | 100.0000 | 231,840.5442 | -231,840.5442 | 20458 |
| always_zero | zero_reference | not_applicable | common_active20 | overall | all | 49183 | 137 | 351,047.4102 | 1,480,879.9105 | 100.0000 | 351,047.4102 | -351,047.4102 | 1827 |
| drop_zero_targets | OLS | nonnegative | all_eligible | overall | all | 75390 | 210 | 41,699.9000 | 101,247.4596 | 17.9865 | 41,699.9000 | 2,073.2038 | 20458 |
| drop_zero_targets | OLS | nonnegative | common_active20 | overall | all | 49183 | 137 | 59,228.7768 | 124,413.3453 | 16.8720 | 59,228.7768 | 2,271.9923 | 1827 |
| replace_zero_history | OLS | nonnegative | all_eligible | overall | all | 75390 | 210 | 60,426.6088 | 128,710.8426 | 26.0639 | 60,426.6088 | 12,279.8031 | 20458 |
| replace_zero_history | OLS | nonnegative | common_active20 | overall | all | 49183 | 137 | 71,890.4731 | 138,115.9420 | 20.4789 | 71,890.4731 | 754.4261 | 1827 |
| replace_zero_history | seasonal_naive | not_applicable | all_eligible | overall | all | 75390 | 210 | 80,696.8266 | 165,815.1400 | 34.8070 | 80,696.8266 | 41,493.6802 | 20458 |
| replace_zero_history | seasonal_naive | not_applicable | common_active20 | overall | all | 49183 | 137 | 88,471.6827 | 168,473.5407 | 25.2022 | 88,471.6827 | 29,491.4434 | 1827 |
| retain_zero | OLS | nonnegative | all_eligible | overall | all | 75390 | 210 | 41,100.6152 | 101,217.6588 | 17.7280 | 41,100.6152 | 302.2317 | 20458 |
| retain_zero | OLS | nonnegative | common_active20 | overall | all | 49183 | 137 | 58,959.3315 | 124,385.4316 | 16.7953 | 58,959.3315 | 585.1851 | 1827 |
| retain_zero | seasonal_naive | not_applicable | all_eligible | overall | all | 75390 | 210 | 51,627.8014 | 128,402.4628 | 22.2687 | 51,627.8014 | -177.3384 | 20458 |
| retain_zero | seasonal_naive | not_applicable | common_active20 | overall | all | 49183 | 137 | 74,370.4508 | 157,772.8545 | 21.1853 | 74,370.4508 | -291.4961 | 1827 |

## Training samples

| policy | training_rows | excluded_training_rows | training_ports | zero_training_targets |
| --- | --- | --- | --- | --- |
| retain_zero | 453180 | 0 | 210 | 124657 |
| drop_zero_targets | 328523 | 124657 | 201 | 0 |
| replace_zero_history | 453180 | 0 | 210 | 124657 |
| active20 | 295646 | 157534 | 137 | 10982 |

## Paired date-block sensitivity

Negative difference favours the alternative; intervals are conditional descriptive bootstrap estimates, not proof of causality or generalisation.

| policy_minus_retain | clipping | cohort | MAE_difference | ci_low | ci_high | block_days | replicates |
| --- | --- | --- | --- | --- | --- | --- | --- |
| drop_zero_targets | nonnegative | all_eligible | 599.2848 | 574.4401 | 626.8620 | 7 | 2000 |
| drop_zero_targets | nonnegative | all_eligible | 599.2848 | 580.3799 | 618.8800 | 28 | 2000 |
| drop_zero_targets | nonnegative | all_eligible | 599.2848 | 582.8774 | 609.1473 | 56 | 2000 |
| drop_zero_targets | none | all_eligible | 487.8314 | 462.7685 | 515.5625 | 7 | 2000 |
| drop_zero_targets | none | all_eligible | 487.8314 | 469.3835 | 507.3457 | 28 | 2000 |
| drop_zero_targets | none | all_eligible | 487.8314 | 471.8499 | 497.5760 | 56 | 2000 |
| replace_zero_history | nonnegative | all_eligible | 19,325.9935 | 18,492.8797 | 20,191.2248 | 7 | 2000 |
| replace_zero_history | nonnegative | all_eligible | 19,325.9935 | 17,836.4134 | 20,610.1669 | 28 | 2000 |
| replace_zero_history | nonnegative | all_eligible | 19,325.9935 | 18,159.7983 | 20,587.5247 | 56 | 2000 |
| replace_zero_history | none | all_eligible | 36,180.5867 | 35,387.3998 | 36,987.3888 | 7 | 2000 |
| replace_zero_history | none | all_eligible | 36,180.5867 | 34,836.3870 | 37,389.1728 | 28 | 2000 |
| replace_zero_history | none | all_eligible | 36,180.5867 | 35,154.4408 | 37,416.1351 | 56 | 2000 |
| active20 | nonnegative | common_active20 | -15.7880 | -23.4339 | -9.1871 | 7 | 2000 |
| active20 | nonnegative | common_active20 | -15.7880 | -21.9778 | -10.1838 | 28 | 2000 |
| active20 | nonnegative | common_active20 | -15.7880 | -20.8202 | -10.4808 | 56 | 2000 |
| active20 | none | common_active20 | -8.4374 | -16.2464 | -1.6979 | 7 | 2000 |
| active20 | none | common_active20 | -8.4374 | -14.6151 | -2.6278 | 28 | 2000 |
| active20 | none | common_active20 | -8.4374 | -13.4195 | -2.8597 | 56 | 2000 |
