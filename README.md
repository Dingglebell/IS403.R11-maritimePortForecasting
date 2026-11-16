# Predictive Modeling of Maritime Port Activity for Operational Capacity Planning in Southeast Asia

IS403.R11 · Group 5 · 2026

Predict each port’s **total estimated cargo volume over the next 7 days**, in tonnes, from daily IMF PortWatch history. Cargo is `import + export`. Compare seasonal naïve, three regression baselines, Random Forest and Histogram Gradient Boosting. SARIMA/SARIMAX with oil prices is optional.

**Status:** Task 1 data preparation and Task 2's feature and four-baseline pipeline are implemented and validated. Định and Hiếu still need to review the shared cohort and clipping rule. No test scores have been produced. Raw data, learning tables and large prediction files stay local.

## Start here

1. Read [the project plan and next steps](docs/project_plan.md).
2. Open [your task brief](docs/tasks.md), then agree the shared [experiment protocol](docs/protocol.md).
3. Follow the [beginner Git Bash guide](docs/git_bash_guide.md). A [one-page printable guide](docs/Git_Bash_Guide.pdf) is included.

## Four folders

```text
data/       Local data and data provenance notes
src/        Preparation, feature and baseline code; later models added here
results/    Small reproducible tables, figures and experiment records
docs/       Task briefs, protocol, paper and slide material
```

Keep one script per workflow stage; add folders only when needed. Raw data, large predictions and trained models stay out of Git by default. See [data access](data/README.md) and [script responsibilities](src/README.md).

## Set up the data

Use Python 3.12.14 and install the pinned dependencies:

```bash
python -m pip install -r requirements.txt
```

Hân's supplied raw files are in `data/chua_xu_ly/` and the reviewed clean CSV is `data/da_xu_ly/ports_daily.csv`. All ten raw hashes and the clean-panel hash match Task 1. To rebuild the clean panel if needed:

```bash
python src/prepare_data.py --input-dir data/chua_xu_ly --output data/ports_daily.csv
```

The cleaner checks the seven-column schema, keys, numeric values and calendar, computes cargo as published import plus export, and preserves observed zeros and unknown measurements. See the [data dictionary](data/data_dictionary.md) for details. Cleaning and Task 2 need no source `snapshot.json`.

## Reproduce the Task 1 audit

The full audit also needs Hân's original `snapshot.json` beside the ten raw CSVs. That metadata file is absent from the currently supplied folders; obtain it before running the audit. With the original archived layout:

```bash
python src/analyze_task1.py --raw-dir data/raw/hdx_2026-10-18
```

Use the exact frozen snapshot. Newly downloaded data may be revised.

Read the [Vietnamese handoff guide](docs/task1_handoff.md), [complete data dictionary](data/data_dictionary.md), [English paper section](docs/data_eda.md) and [zero-handling study](docs/zero_handling.md). The main diagnostic scores 75,390 common validation origins: retaining zeros yields OLS MAE 41,100.62 tonnes, versus 41,699.90 after dropping zero training labels and 60,426.61 after causal zero-history replacement. This finding is scoped to the documented model and original estimated targets; it is not proof that every zero is physically correct. The 20% eligibility sensitivity and country exceptions are disclosed separately.

The full clean panel has 594,720 rows. The recommended `selected_ports.csv` retains 210 complete-training-coverage IDs, with the alternative 137-port rule recorded as a candidate flag. Shared rule approval is not assumed. See the [audit](results/data_audit.md) and [validation tables](results/zero_validation.md). Do not compare scores from different populations to select a rule. CSV datasets remain local per repository policy.

## Run Task 2

Định and Hiếu can run features, chronological splits and the four baseline models with the reviewed clean panel:

```bash
python -m unittest discover -s src -p 'test_*.py' -v
python src/run_task2.py --panel data/da_xu_ly/ports_daily.csv
```

This uses Hân's supplied processed CSV, verifies the Task 1 panel hash, builds the common train/validation table, and exports predictions, metrics and a run record. If you instead place the canonical clean panel at `data/ports_daily.csv`, omit `--panel`. It scores validation only and reports raw and nonnegative variants while the shared rules remain pending. Read the [Task 2 pipeline and work split](docs/task2_pipeline.md) and the [English methods draft](docs/features_baselines.md).

The verified run has 453,180 training rows and 75,390 validation rows per model across 210 ports. See the [baseline comparison](results/baseline_validation.md). Small result summaries and figures are tracked; large datasets, prediction files and row-level exclusion lists are ignored so `git add -A` stages the shareable project files.

Step 2's [feature and split review](results/task2_feature_review.md) includes an independent check of every learning row, a Hải Phòng hand calculation and concrete boundary exclusions. It is ready for Hiếu's peer review; reproduce it with the commands in the [Task 2 guide](docs/task2_pipeline.md#step-2-review-for-định-and-hiếu).

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
