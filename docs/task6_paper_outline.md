# English research paper outline

Working title: Predictive Modeling of Maritime Port Activity for Operational Capacity Planning in Southeast Asia.

Write the full paper after experiments. Do not invent scores, findings or data-quality claims. Use Times New Roman 13, black text and gray table headers in the final document. Confirm the instructor’s submission template and reference style.

| Section | Lead contribution | Content |
|---|---|---|
| Abstract | All, after results | Problem, data, fair comparison, main measured finding, limitation |
| Introduction | All | Operational need, seven-day target, study questions and scope |
| Related Work | Huy, Tiến | Three studies, differences in frequency and units, adopted ideas |
| Data and Exploratory Analysis | Hân | Provenance, panel audit, zero days, train-only port selection |
| Feature Engineering and Baselines | Định, Hiếu | Origin, windows, leakage checks and four baselines |
| Machine Learning Methods and Experimental Setup | Huy, Tiến | RF/HGB, tuning, feature comparisons, chronological splits |
| Results | Hân, Định, Hiếu | Same-row metrics, port/country breakdowns and forecast plots |
| Discussion and Business Implications | Hân, Định, Hiếu | Failure cases, operational interpretation and limits |
| Conclusion | All | Answer research questions; avoid unsupported recommendations |
| References | Tiến coordinates | Verified originals and data/software sources |

Suggested research questions: Do learned models beat seasonal naïve? Do port calls and 28-day activity improve forecasts? How does performance vary by country and port activity? Include optional SARIMA/SARIMAX only if evaluated fairly.

Essential figures/tables: data audit, split timeline, feature definitions, overall comparison, subgroup comparison, observed-versus-predicted example. Tie each to a reproducible output file. Explain that PortWatch cargo is estimated and forecasting demand does not measure actual capacity.
