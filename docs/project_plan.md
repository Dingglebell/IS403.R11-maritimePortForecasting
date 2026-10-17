# Project plan and next steps

The two source tables use different dates. Preserve both: stage dates are initial progress targets; assignment dates are working handoff deadlines for this repository. This is a scheduling proposal to confirm at the next meeting, not a claim that the instructor changed a deadline. Dates are interpreted as 2026 from the project term.

## Project stages

| Stage | Main work | Expected result | Original target |
|---|---|---|---|
| 1 | Review three papers and agree the problem | Related-work notes and shared design | 20 October |
| 2 | Audit and prepare PortWatch | Clean data, port list and EDA | 25 October |
| 3 | Features, time splits and baselines | Learning table and baseline results | 1 November |
| 4 | Tree models and optional extension | Configurations and forecasts | 8 November |
| 5 | Evaluate and interpret | Metrics, plots and planning implications | 15 November |
| 6 | Integrate and rehearse | English paper, at most 30 slides and code | 27 December |

## Corresponding assignments

| Task | Owners | Stage | Handoff | Main output |
|---|---|---|---|---|
| 1 | Hân | 2 | 25 October | Clean panel and Data and Exploratory Analysis |
| 2 | Định, Hiếu | 3 | 8 November | Features, splits and baseline results |
| 3 | Huy, Tiến | 4 | 25 November | RF, HGB and experimental setup |
| 4 | Huy, Tiến | 4 | 1 December | Related Work and extension decision |
| 5 | Hân, Định, Hiếu | 5 | 15 December | Results, Discussion and Business Implications |
| 6 | All five members | 6 | 27 December | Paper, slides and reproducible repository |

Stage 1 has no separate named assignment row. Proposed owners are the whole group for scope decisions and Huy/Tiến for initial literature notes. Their full Related Work handoff remains 1 December. Stage 4 has two separate task briefs because the source assigns core models and the optional extension separately.

## Immediate next steps

1. **17–20 October:** Định coordinates repository access and a short scope meeting. Each member clones the repository and submits one small practice change. The owner adds the four teammates after collecting their GitHub usernames.
2. **By 20 October:** the group confirms the schedule, forecast availability convention, core country scope and cutoff dates. Huy/Tiến provide short notes on the three papers. Leave Laos national trade, weather and other targets outside the core port forecast.
3. **By 25 October:** Hân locates the exact downloaded snapshot, records its provenance and hash, verifies the schema, audits zero days and hands off a first clean panel. Định/Hiếu help establish training dates before port selection.
4. **Next:** Định/Hiếu verify features on one port and one hand-worked example, then run naïve and regression on validation. Huy/Tiến can prepare model code using the agreed schema while waiting.
5. **After baseline review:** freeze evaluation rows, run RF/HGB and feature comparisons, and decide on SARIMA/SARIMAX only if it fits the remaining time. Freeze all choices before final test scoring.
6. **16–27 December:** integrate the English paper, verify a fresh-clone run and rehearse the deck. Confirm submission format and presentation duration.

## Decisions to record at the first meeting

- Exact dataset file, source/download date, license, fields, daily timestamp convention and any publication delay.
- Exact train/validation/test calendar boundaries and training-only port eligibility rule.
- Who integrates the paper and slides, reviewer rotation, and treatment of the conflicting stage targets.

The current setup contains no training data or results. Snapshot counts in the introductions are claims to reproduce, not assumptions for the final paper.
