# Predictive Modeling of Maritime Port Activity for Operational Capacity Planning in Southeast Asia

IS403.R11 · Group 5 · 2026

Predict each port’s **total estimated cargo volume over the next 7 days**, in tonnes, from daily IMF PortWatch history. Cargo is `import + export`. Compare seasonal naïve, three regression baselines, Random Forest and Histogram Gradient Boosting. SARIMA/SARIMAX with oil prices is optional.

**Status:** Task 1 cleaning, dictionary, provenance audit, training-based port lists, EDA and controlled zero-handling validation are implemented. The English paper section is ready for review. Joint Task 2 review and final rule freeze are pending; no test scores have been produced. Raw data, the clean panel and large diagnostic tables remain local.

## Start here

1. Read [the project plan and next steps](docs/project_plan.md).
2. Open [your task brief](docs/tasks.md), then agree the shared [experiment protocol](docs/protocol.md).
3. Follow the [beginner Git Bash guide](docs/git_bash_guide.md). A [one-page printable guide](docs/Git_Bash_Guide.pdf) is included.

## Four folders

```text
data/       Local data and data provenance notes
src/        Future preparation, feature, model and evaluation code
results/    Small reproducible tables, figures and experiment records
docs/       Task briefs, protocol, paper and slide material
```

Keep one script per workflow stage; add folders only when needed. Raw data, large predictions and trained models stay out of Git by default. See [data access](data/README.md) and [planned script interfaces](src/README.md).

## Reproduce Task 1

With Python 3.12.14 and the raw country CSVs in `data/raw/hdx_2026-10-18`, run:

```bash
python -m pip install -r requirements.txt
python src/prepare_data.py --input-dir data/raw/hdx_2026-10-18 --output data/ports_daily.csv
python -m unittest discover -s src -p 'test_*.py' -v
python src/analyze_task1.py --raw-dir data/raw/hdx_2026-10-18
```

The cleaning script maps source fields to the agreed seven-column schema, checks keys and numeric values, and computes cargo as published import plus export. It retains observed zeros and represents missing dates or measurements as missing. Ambiguous duplicates and invalid values stop processing for investigation. Source timestamps are midnight UTC observation labels; no local-date shift is applied. Cleaning alone requires no JSON. The analysis stage uses the original local `snapshot.json` and shared `experiment.json` to verify provenance and reproduce the diagnostic. Use the exact frozen snapshot; current downloads may differ.

Read the [Vietnamese handoff guide](docs/task1_handoff.md), [complete data dictionary](data/data_dictionary.md), [English paper section](docs/data_eda.md) and [zero-handling study](docs/zero_handling.md). The main diagnostic scores 75,390 common validation origins: retaining zeros yields OLS MAE 41,100.62 tonnes, versus 41,699.90 after dropping zero training labels and 60,426.61 after causal zero-history replacement. This finding is scoped to the documented model and original estimated targets; it is not proof that every zero is physically correct. The 20% eligibility sensitivity and country exceptions are disclosed separately.

The full clean panel has 594,720 rows. The recommended `selected_ports.csv` retains 210 complete-training-coverage IDs, with the alternative 137-port rule recorded as a candidate flag. Shared rule approval is not assumed. See the [audit](results/data_audit.md) and [validation tables](results/zero_validation.md). Do not compare scores from different populations to select a rule. CSV datasets remain local per repository policy.

## Team

| Member | Main assignments |
|---|---|
| Nguyễn Thị Quỳnh Hân | Tasks 1, 5, 6 |
| Phạm Công Định | Tasks 2, 5, 6 |
| Lê Nguyễn Hữu Hiếu | Tasks 2, 5, 6 |
| Trần Hoàng Huy | Tasks 3, 4, 6 |
| Lê Minh Tiến | Tasks 3, 4, 6 |

## Collaboration

Use a branch for each change and open a pull request into `main`. Another member reviews the change. For paired assignments, use separate branches when editing the same files. Include the purpose, files changed and validation in each pull request. These are team conventions, not configured GitHub branch restrictions.

## Final submission

An English research paper, no more than 30 slides, source code, data provenance and verified run instructions. Documents use Times New Roman 13, black text and gray table headers. The formatted PDFs follow this style; GitHub controls Markdown display fonts. See the [paper outline](docs/paper_outline.md) and [26-slide outline](docs/slides_outline.md).

The current request determines scope. The supplied work plan determines named assignments; earlier introduction requirements and unverified snapshot counts are background, not new commands. See [sources](docs/references.md).
