# Extension decision: SARIMA and SARIMAX

Status: validation only. Test cargo was not read; observations after 31 December 2025 were dropped before any computation.

## Decision

| Extension | Decision | Reason in one line |
|---|---|---|
| **SARIMA** (history only), per port, on a training-selected subset | **Go. Implemented and evaluated on validation.** | Cheap to run (about 6 minutes for 67 ports on two cores), no missing values, and a fair same-row comparison is possible. |
| **SARIMAX** with an oil-price regressor | **No-go for now. Not implemented.** | No oil series is in the repository, none could be downloaded in the working environment, and published evidence does not show that oil alone helps. Re-open conditions are listed below. |

## Evidence by criterion

| Criterion | SARIMA | SARIMAX with oil |
|---|---|---|
| Coverage | The 67 ports of the training-defined `high` activity group (training active share at least two thirds) have complete daily history. Fitted 67 of 67; nothing excluded. Low- and medium-activity ports were not tried: their series are mostly zeros and SARIMA assumes a continuous series. | Public WTI daily prices exist (U.S. EIA, shown on FRED as series DCOILWTICO), but no oil file is in the repository or the panel, and the working shell cannot download it. Nothing could be audited beyond the series' public page. |
| Frequency | Daily series, weekly seasonal period 7, matching the daily panel. | Daily WTI matches the panel frequency. The only published SARIMAX study we read (Lee and Bang) used monthly throughput and did not state its oil series' frequency, so its design does not transfer directly. |
| Publication timing | Uses only the port's own cargo through the origin date. | The FRED page showed the latest observation dated 17 November 2026 with a last update on 18 November, so about one day of lag (inferred from those dates, not a stated policy), and states that data are subject to revision. A monthly series would not be known until after the month ends. Any oil input must be lagged to what was published at the origin. |
| Missing values | None in the panel for these ports. | Cannot be assessed without the file. Non-trading days (weekends, holidays) would need an explicit rule. |
| Future exogenous path | Not needed. | Needed for the seven forecast days. It must be a stated scenario (for example holding the last published price constant) or a forecast; realised future prices are not allowed. The reference study does not clearly say how it handled this. |
| Runtime | 353.5 s for 67 ports (about 10 s per port for three candidate fits plus 359 rolling forecasts, on two cores). | Expected to be similar to SARIMA, but unmeasured. |
| Expected value | Established time-series benchmark for the target. | In Lee and Bang's 2022 test, WTI alone was worse than plain SARIMA (MAPE 3.66% against 3.02%); only the combination with China's exports helped, and that winning model had a worse AIC than SARIMA. The link between oil price and seven-day cargo at individual ports is untested. |
| Core models complete | Task 2 baselines and Task 3 validation results exist. They have not been jointly reviewed or merged, and test is not scored. | Same. |

## What was run

`src/sarimax.py` fits, for each port, one SARIMA model on observations through 31 December 2024. The order is chosen by training AIC from three candidates: (1,0,0)(1,0,0)7, (1,0,1)(1,0,1)7 and (2,0,1)(1,0,1)7, with a constant, on the series divided by its training mean. Parameters are not refitted during validation. At each of the 359 validation origins (31 December 2024 to 24 December 2025) the forecast uses data through that origin, and the seven daily forecasts are summed to the seven-day total. Predictions are clipped at zero with the raw version kept in `extension_none_predictions.csv`. Chosen orders: 6 ports (1,0,0), 27 ports (1,0,1) and 34 ports (2,0,1). The optimiser did not report convergence for 3 ports; they stayed in the comparison.

## Same-subset comparison (validation, 67 ports, 24,053 identical port-origin rows)

MAE and RMSE in tonnes per seven-day target; nonnegative forecasts for every model.

| Model | Feature set | MAE | RMSE | WAPE % |
|---|---|---:|---:|---:|
| Multivariate regression | all_three | **96,124** | **171,554** | **14.4** |
| **SARIMA** | cargo history | 99,829 | 205,162 | 15.0 |
| Random Forest | all_three | 103,519 | 217,551 | 15.5 |
| HGB | all_three | 107,060 | 225,842 | 16.1 |
| Seasonal naïve | cargo_only | 121,861 | 217,781 | 18.3 |

Reading the table:

1. SARIMA beats seasonal naïve by 18.1% in MAE and beats RF and HGB on the subset, but is 3.9% worse than multivariate regression pooled.
2. The pooled figure is dominated by one port. `port1201` (Singapore) carries 37.1% of the subset's cargo. There regression has MAE 697,643 against 1,115,607 for SARIMA. Without `port1201`, SARIMA is best: 84,438 against 87,010 for regression, 86,482 for RF, 89,384 for HGB and 110,462 for naïve.
3. Port by port, SARIMA has lower MAE than regression in 52 of 67 ports, than RF in 49, than HGB in 47 and than naïve in 64. The median per-port MAE is 66,880 for SARIMA and 69,669 for regression.
4. Regression stays lower pooled in each of the seven non-overlapping origin phases (94,522–97,326 tonnes against 98,904–100,658 for SARIMA).

## Caveats

- This is validation for one year. It is not a test result and gives no significance claim; daily seven-day windows overlap.
- SARIMA's order was chosen on training AIC only, whereas RF and HGB settings were tuned on validation MAE, which slightly favours the tree models.
- SARIMA uses each port's full recent series state; the other models use three summary features of that history. The comparison shows what each approach achieves, not which structure is intrinsically better.
- Results apply to the `high` activity group only and say nothing about the 143 medium- and low-activity ports.
- Parameters are not refitted during validation, matching the other models; refitting could change the ranking.
- Order candidates are few and fixed. The 3 non-converged fits were not investigated further.

## Conditions to re-open SARIMAX

1. The group supplies a daily oil file (for example WTI from FRED) with its download date and source terms, which is then added to the data manifest.
2. The input at origin t is the last price published by t (lagged at least one day). The horizon path is held at that value as a stated scenario; realised future prices are never used.
3. The model is fitted on the same 67 ports and origins, compared with the SARIMA above and the core models, and reported whether or not it helps.

If the group does not supply the file before the paper is finalised, the paper should report SARIMAX as examined and not pursued, for the reasons in this document.

## Outputs

`results/extension_predictions.csv` (nonnegative, schema from `docs/protocol.md`; `model=sarima`, `feature_set=cargo_history`), `results/extension_none_predictions.csv` (raw), `results/extension_port_fits.csv` (chosen order, training AIC, convergence flag and seconds per port), `results/extension_run.json` (settings, versions, runtime and subset metrics) and `results/extension_subset_comparison.csv` (the comparison above plus the remaining core variants). Prediction files are large and stay local, as in Tasks 2 and 3.

Reproduce:

```bash
python -m pip install -r requirements.txt
python src/sarimax.py --panel data/da_xu_ly/ports_daily.csv --table data/learning_table.csv --out-dir results
```

`sarimax.py` writes the prediction, port-fit and run files. `extension_subset_comparison.csv` was built separately by joining these predictions with the Task 2 and Task 3 prediction files on the same 24,053 keys; that join script is not yet in the repository.

Reproducibility note: an independent rerun on Python 3.12 with SciPy 1.18.1 gave SARIMA MAE 99,705 instead of 99,829 (0.12% lower). Three ports (port111, port1273, port309) chose (1,0,1) instead of (2,0,1) because the optimiser converged slightly differently. Every ranking and conclusion above is unchanged. The core-model rows of the comparison reproduced exactly.
