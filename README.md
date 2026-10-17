# Predictive Modeling of Maritime Port Activity for Operational Capacity Planning in Southeast Asia

IS403.R11 · Group 5 · 2026

Predict each port’s **total estimated cargo volume over the next 7 days**, in tonnes, from daily IMF PortWatch history. Cargo is `import + export`. Compare seasonal naïve, three regression baselines, Random Forest and Histogram Gradient Boosting. SARIMA/SARIMAX with oil prices is optional.

**Status:** collaboration starter repository. Task briefs, experiment rules and writing outlines are ready. The data snapshot and modelling code are not included yet; no model results are claimed.

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
