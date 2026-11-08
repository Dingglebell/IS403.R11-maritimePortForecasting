# Task 2 validation results

Validation only. The shared cohort and clipping rule still require team agreement.

Working output clipping: none. Both raw and nonnegative variants are exported separately.

| Model | Clipping | Rows | MAE tonnes | RMSE tonnes | WAPE percent |
|---|---|---:|---:|---:|---:|
| seasonal_naive | none | 75,390 | 51,627.80 | 128,402.46 | 22.2687 |
| linear_univariate | none | 75,390 | 51,926.57 | 128,248.51 | 22.3975 |
| linear_multivariate | none | 75,390 | 41,212.07 | 101,220.29 | 17.7760 |
| polynomial_degree2 | none | 75,390 | 52,369.56 | 128,114.94 | 22.5886 |
| seasonal_naive | nonnegative | 75,390 | 51,627.80 | 128,402.46 | 22.2687 |
| linear_univariate | nonnegative | 75,390 | 51,926.57 | 128,248.51 | 22.3975 |
| linear_multivariate | nonnegative | 75,390 | 41,100.62 | 101,217.66 | 17.7280 |
| polynomial_degree2 | nonnegative | 75,390 | 52,369.56 | 128,114.94 | 22.5886 |

Lowest validation MAE in the working output: linear_multivariate. This is not a test conclusion.

All four models use identical port-origin rows. Negative raw forecasts are disclosed; no test scores are generated.
Daily seven-day target windows overlap. Do not sum them as independent weekly cargo totals.
