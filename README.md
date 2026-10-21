# Predictive Modeling of Maritime Port Activity for Operational Capacity Planning in Southeast Asia

IS403.R11 · Group 5 · 2026

Predict each port’s **total estimated cargo volume over the next 7 days**, in tonnes, from daily IMF PortWatch history. Cargo is `import + export`. Compare seasonal naïve, three regression baselines, Random Forest and Histogram Gradient Boosting. SARIMA/SARIMAX with oil prices is optional.

**Status:** Task 1 panel preparation, data audit, EDA, training-only candidate selection and a validation-only eligibility sensitivity are implemented. The user confirmed Dinh/Hieu's agreement to the dates. Joint review and final port-rule freezing remain pending. Raw data, derived panels and large predictions stay local and ignored by Git. The sensitivity is not Task 2's production baseline comparison or final test scoring.

## Start here

1. Read [the project plan and next steps](docs/project_plan.md).
2. Open [your task brief](docs/tasks.md), then agree the shared [experiment protocol](docs/protocol.md).
3. Follow the [beginner Git Bash guide](docs/git_bash_guide.md). A [one-page printable guide](docs/Git_Bash_Guide.pdf) is included.

## Four folders

```text
data/       Local data and data provenance notes
src/        Preparation, checks and future feature, model and evaluation code
results/    Small reproducible tables, figures and experiment records
docs/       Task briefs, protocol, paper and slide material
```

Keep one script per workflow stage; add folders only when needed. Raw data, large predictions and trained models stay out of Git by default. See [data access](data/README.md) and [planned script interfaces](src/README.md).

## Run Task 1

Use Python 3.12.14 (the tested version) with `requirements.txt`. In an activated virtual environment, run from the repository root:

```bash
python -m pip install -r requirements.txt
python src/download_portwatch.py --output-dir data/raw/hdx_2026-10-18 --verify-only --manifest data/manifest.csv
python src/prepare_data.py --snapshot data/raw/hdx_2026-10-18/snapshot.json --experiment experiment.json --output-dir data --results-dir results --eda-doc docs/data_eda.md --select-ports
python src/validate_port_rules.py --panel data/ports_daily.csv --experiment experiment.json --results-dir results
python src/verify_task1.py
```

The commands above were exercised on the local snapshot. Obtain the raw files using [the documented access steps](docs/data_access.md) if they are not already available. Public download URLs may change in place; compare with the [recorded file hashes](docs/portwatch_snapshot_manifest.json). Preparation rejects a snapshot that differs from the hash already recorded in `experiment.json`.

Outputs are `data/ports_daily.csv`, `data/selected_ports.csv`, the [data dictionary](data/data_dictionary.md), [audit report](results/data_audit.md), three figures and the [English Data and Exploratory Analysis section](docs/data_eda.md). The full panel preserves all 210 source IDs and reported zeros; the candidate list retains 137 IDs, with 23 low-, 47 medium- and 67 high-activity ports based on 2019-2024 only. All 10 coastal countries remain represented. Every excluded ID has a reason in the local selection audit.

The checks exercise unknown versus zero observations, calendar gaps, source reconciliation, training-only selection, hand-worked feature/target windows, label boundaries, metrics and identical validation keys. Integration checks require local preparation and validation outputs; run the commands in order. The verifier refuses to record success with skipped checks and writes the complete test list and hashes to `results/task1_verification.json`. The suite can also be run directly with `python -m unittest discover -s src -p 'test_*.py' -v`.

`experiment.json` records training 2019-01-01–2024-12-31, validation 2025-01-01–2025-12-31 and test 2026-01-01–2026-10-02. Han explicitly confirmed both teammates' agreement on 20 October; these exact dates were not inferred from the Word proposal. `--select-ports` requires that recorded agreement. It also requires explicit candidate settings, but does not invent approval of a candidate or validation result.

The [eligibility sensitivity](results/eligibility_validation.md) compares coverage-only eligibility with the protocol's >=20% active-day candidate on the same 49,183 validation keys. A fixed pooled linear diagnostic gives the 20% candidate a very small MAE advantage, with slightly worse RMSE; it supports review, not a robust superiority claim. Test measurements are discarded before any diagnostic window is constructed. [The handoff](docs/task1_handoff.md) identifies the remaining joint review and freeze. Task 2's production learning table, four-baseline comparison and final test scoring remain separate work. [Vietnamese handoff guidance](docs/huong_dan_ban_giao_task1.md) is available for Han.

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
