# Related work

This section summarises three studies that motivate the project and states what we adopt from each. The studies forecast different targets at different frequencies, so we use them for design ideas and caution, not as results to reproduce or compare against.

**Verification status.** All three studies were read in full. Xu et al. (2022) and Lee and Bang (2024) are open-access, and every number quoted below was re-checked against the publisher pages on 24 November 2026, including the Lee and Bang tables. Nakashima and Shibasaki (2024) was checked against the published PDF obtained through a team member's access.

## 1. Xu et al. (2022): machine learning versus conventional methods

- **Question.** Which of several existing methods forecasts port container throughput most accurately when all are applied to the same series?
- **Data.** Annual container throughput of the world's top 20 ports from the ports' official websites, 2004–2020: 17 observations per port, 13 for training (2004–2016) and 4 for testing (2017–2020). The text we read does not state the unit. No exogenous variables.
- **Methods.** Four conventional methods (naïve, moving average, autoregression, ARIMA) and five neural methods (MLP, GRU, LSTM, CNN, Transformer).
- **Findings.** GRU had the lowest test MAPE for 17 of 20 ports (abstract range 0.54–2.27 MAPE), ARIMA for two and Transformer for one. Average MAPE was 7.89 for the machine-learning group and 8.39 for the conventional group. The authors conclude that machine learning is not necessarily better and suggest the naïve method for quick estimates.
- **Limitations.** Very short series, 20 ports, history-only inputs. The authors state the conclusions apply to series with similar short, sparse characteristics. In our reading the methods section lists an RNN while the results discuss GRU and LSTM; check this before citing the method list.
- **What we adopt.** A naïve forecast as a mandatory benchmark and a same-row comparison of simple and learned models. Their caution that more complex models do not always win matches our measured result that regression beat both tree models. We do not adopt neural networks or annual data.

## 2. Lee and Bang (2024): SARIMAX with exogenous variables for Singapore

- **Question.** Does adding exogenous variables to a seasonal ARIMA model improve forecasts of monthly container throughput at the Port of Singapore?
- **Data.** Monthly throughput in TEU from the Singapore Department of Statistics, fitted on January 2010 to December 2021 and tested on the 12 months of 2022. Candidate exogenous variables: WTI crude oil price (U.S. EIA), China's export volume (FRED) and global COVID-19 cases (WHO). The paper does not state the exogenous series' frequency.
- **Methods.** SARIMA with seasonal period 12, order chosen by AIC and BIC; SARIMAX versions with each exogenous variable; eleven benchmarks, including Holt–Winters, linear/LASSO/Ridge regression, Random Forest, XGBoost, LightGBM, LSTM and Prophet. Final model SARIMAX(0,1,1)(1,1,1)12 with WTI and China exports.
- **Findings (2022 forecasts).** SARIMAX with both variables had the lowest errors: MAPE 2.34%, MAE 72.27, RMSE 92.99, against 3.02%, 91.97 and 117.21 for plain SARIMA. WTI alone was worse than plain SARIMA (MAPE 3.66%). COVID-19 cases were dropped. Random Forest (2.91%), Prophet (2.94%) and LightGBM (2.98%) also had slightly lower MAPE than plain SARIMA.
- **Limitations.** The authors note that forecasting with exogenous variables requires forecasting those variables. The paper does not clearly say how the 2022 exogenous values were obtained; benchmarks used the same predictors, which suggests, but does not confirm, that realised 2022 values were used. By our reading the text and Table 1 give different AIC figures for the selected SARIMA model; check before citing. The winning model had a worse AIC than plain SARIMA and was selected on 12 test months.
- **What we adopt.** The SARIMA/SARIMAX framework as an optional extension, and their warning about exogenous inputs: only values known at the forecast origin may be used, and future paths must be forecast or stated as scenarios. We use a weekly seasonal period of 7, not 12. Because oil alone did not help in their test, we do not assume it will help here.

## 3. Nakashima and Shibasaki (2024): AIS data for weekly dry bulk throughput

- **Question.** Can variables derived from AIS vessel-tracking data improve the accuracy of short-term forecasts of weekly port cargo throughput?
- **Data.** Weekly iron ore exports in tonnes, taken from AXS Dry, a commercial trade-flow database that estimates port throughput from AIS records. It is published only after a delay of a few months. The main target is Port Hedland (Australia), with Ponta da Madeira (Brazil) as a second case. Training covers week 1 of 2016 to week 26 of 2019, which is 182 weeks per port. Because that is short, the authors pool eight similar large iron ore ports to reach 1,638 training weeks. Other inputs are AIS records of 1,117 Capesize bulk carriers (Lloyd's List Intelligence) and weekly averages of iron ore futures prices.
- **Methods.** An LSTM forecasts throughput three weeks ahead from the previous 26 weeks of inputs; the horizon was chosen from interviews with shipping companies. Thirteen AIS variables were tested one at a time against a baseline LSTM that uses only throughput histories and futures prices, and ranked by their MAPE improvement over 26 test weeks (second half of 2019).
- **Findings.** Four variables improved MAPE by more than five percentage points: vessel traffic at port level and at regional level around the target port, vessel traffic around the largest partner import port, and the past year's vessel traffic around the target port. Berth use, vessel speed and draught change helped little. For Port Hedland the selected model reached 9.3% MAPE against 25.0% for the baseline LSTM. The paper calls this gap 14.7 points, although the two figures differ by 15.7; cite the two MAPE values rather than the gap. On the first half of 2020 (COVID-19 period), MAPE was 10.7% for Port Hedland, 15.1% for Tubarão and 11.8% for Seven Islands, each more than ten points better than the baseline.
- **Limitations.** The throughput data are not available in real time, so real-time use would need a separate AIS-based estimate. Only large iron ore ports and one commodity were studied, and the authors say feature selection, the choice of similar ports and the number of variables need further work. They did not compare the LSTM with other methods, including conventional time-series models. Each test period covers only 26 weeks.
- **What we adopt.** Adding vessel-activity inputs to a short-horizon cargo forecast; our closest counterpart is port calls (`calls_7d`). Their measured value of AIS variables contrasts with our small gain from port calls (about 0.8% MAE once the 28-day mean is present), but our variable is a much simpler count. We also share their practice of pooling ports to enlarge training data and of examining a disruption period. Unlike them, we compare against naïve and regression benchmarks.

## Differences in target, frequency and unit

| | Xu et al. | Lee and Bang | Nakashima and Shibasaki | This project |
|---|---|---|---|---|
| Frequency | Annual | Monthly | Weekly | Daily origins, seven-day target |
| Target | Container throughput (unit not stated in text read) | Container throughput, TEU | Iron ore exports, tonnes (AIS-based estimates) | Estimated cargo, metric tonnes |
| Units covered | 20 ports | One port | Port Hedland and Ponta da Madeira, plus two ports in the 2020 test; eight similar ports pooled | 210 ports and terminals, 10 countries |
| Series length | 17 points per port | 144 months fitted | 182 training weeks per port (1,638 pooled) | 2,192 training days per port |
| Inputs | History only | History plus exogenous series | Throughput history, iron ore futures, AIS-derived variables | Cargo history, port calls |
| Methods | Naïve to neural networks | SARIMAX and ML comparators | LSTM | Regression, RF, HGB; optional SARIMA |

TEU counts standard containers, while PortWatch cargo is an estimated tonnage built from vessel activity; the two are not interchangeable. Annual and monthly series are short, smooth and cannot show weekly operational variation. Our daily panel is long but contains many zeros (54% of port-days), so errors in our units are not comparable with their percentage errors. The project does not reproduce any of these studies.

## Adoption table

| Study | Idea | Used in this project | Not used |
|---|---|---|---|
| Xu et al. | Compare simple and learned models on identical data; keep a naïve benchmark | Seasonal naïve and regression baselines; same-row scoring | Neural networks; annual data |
| Lee and Bang | SARIMA with exogenous drivers; exogenous values must be known or forecast | Optional per-port SARIMA on a training-selected subset; origin-time rule for any exogenous series | Monthly seasonality; oil variable (no-go, see `extension_decision.md`) |
| Nakashima and Shibasaki | Extra vessel-activity inputs for short-horizon forecasts; pooling similar ports | Port calls as a feature set; pooled training across ports; examination of subgroups and shocks in the results stage | AIS processing; LSTM; commodity-specific modelling |

## References

1. Xu, S., Zou, S., Huang, J., Yang, W., and Zeng, F. (2022). Comparison of different approaches of machine learning methods with conventional approaches on container throughput forecasting. *Applied Sciences*, 12(19), 9730. https://doi.org/10.3390/app12199730
2. Lee, G.-C., and Bang, J.-Y. (2024). Forecasting container throughput of Singapore Port considering various exogenous variables based on SARIMAX models. *Forecasting*, 6(3), 748–760. https://doi.org/10.3390/forecast6030038
3. Nakashima, M., and Shibasaki, R. (2024). Can AIS data improve the short-term forecast of weekly dry bulk cargo port throughput? A machine-learning approach. *Maritime Policy & Management*, 51(8), 1788–1804 (published online 14 May 2023). https://doi.org/10.1080/03088839.2023.2212264
