# PortWatch data access and download inventory

Task 1 data acquisition was completed locally on 18 October 2026. The 10 original CSV files are stored in `data/raw/hdx_2026-10-18/`. They contain **594,720 original rows and 210 distinct port IDs**, covering **1 January 2019 through 2 October 2026**. Each file has 29 source columns. A complete CSV scan found no missing date/port/country keys and no duplicate `(portid, date)` keys, including across files. Every SHA-256 matches the download record.

The term port ID follows the source identifier and includes terminals: 44 IDs have source names containing Offshore Oil Terminal. This is made explicit in the data dictionary and audit; no such ID has been excluded using full-snapshot outcomes.

This is a new download from IMF PortWatch via HDX. Matching the preliminary row and port counts does not establish byte identity with the group's reported 12 October snapshot. The older five-country Hugging Face repackaging was not downloaded or combined with these files. Acquisition covers the 10 coastal countries described in the supplied proposal; final study scope still requires team agreement.

## Observed country coverage

| Country source | ISO3 | Original rows | Ports |
|---|---|---:|---:|
| [brunei-darussalam](https://data.humdata.org/dataset/brunei-darussalam-daily-port-activity-data-and-shipment-estimates) | BRN | 5,664 | 2 |
| [cambodia](https://data.humdata.org/dataset/cambodia-daily-port-activity-data-and-shipment-estimates) | KHM | 2,832 | 1 |
| [indonesia](https://data.humdata.org/dataset/indonesia-daily-port-activity-data-and-shipment-estimates) | IDN | 286,032 | 101 |
| [malaysia](https://data.humdata.org/dataset/malaysia-daily-port-activity-data-and-shipment-estimates) | MYS | 116,112 | 41 |
| [myanmar](https://data.humdata.org/dataset/myanmar-daily-port-activity-data-and-shipment-estimates) | MMR | 5,664 | 2 |
| [philippines](https://data.humdata.org/dataset/philippines-daily-port-activity-data-and-shipment-estimates) | PHL | 73,632 | 26 |
| [singapore](https://data.humdata.org/dataset/singapore-daily-port-activity-data-and-shipment-estimates) | SGP | 8,496 | 3 |
| [thailand](https://data.humdata.org/dataset/thailand-daily-port-activity-data-and-shipment-estimates) | THA | 36,816 | 13 |
| [timor-leste](https://data.humdata.org/dataset/timor-leste-daily-port-activity-data-and-shipment-estimates) | TLS | 8,496 | 3 |
| [viet-nam](https://data.humdata.org/dataset/viet-nam-daily-port-activity-data-and-shipment-estimates) | VNM | 50,976 | 18 |

## Provenance and access

`docs/portwatch_snapshot_manifest.json` records the public source URLs, actual direct CSV URLs, file hashes, byte counts, resource modification dates and terms link. The snapshot-local `snapshot.json` retains the full download records and previous attempt errors. Source package metadata is preserved alongside each CSV. `inventory.json` records the complete CSV scan, and `data/manifest.csv` provides the local provenance table. Raw and derived data remain ignored by Git.

HDX identifies the source as IMF PortWatch and describes estimated shipment volumes in metric tonnes and daily port-call counts. Its license is labelled `hdx-other` and points to [IMF copyright and terms](https://www.imf.org/en/about/copyright-and-terms). Preserve attribution and review applicable data terms before any redistribution. No data has been published by this workflow.

For two small files reused after an interrupted first attempt, the original HTTP completion timestamp is unavailable. Their records explicitly leave `downloaded_at_utc` null and retain the actual local file modification time and subsequent verification time. All files were received on 18 October 2026 in Asia/Saigon.

The public resource URLs may be updated in place. Preserve this local snapshot. A future download must be checked against the recorded hashes before being treated as the same dataset.

## Verified commands

Run from the repository root with Python 3.11 or later. These commands use only the Python standard library; this run used Python 3.12.14.

```bash
python src/download_portwatch.py --output-dir data/raw/hdx_2026-10-18 --manifest data/manifest.csv
python src/download_portwatch.py --output-dir data/raw/hdx_2026-10-18 --verify-only --manifest data/manifest.csv
```

The download command refuses to overwrite a recorded snapshot. Use a new directory for a new download. After an interrupted download, `--resume` verifies complete files and preserves incomplete attempts before retrying. Raw bytes are not cleaned or changed. The verifier reads original rows and does not select ports.

## Task 1 preparation and remaining decisions

The preparation workflow now generates the canonical panel, missingness/calendar checks, negative-value checks, cargo totals, zero-day and long-zero-run diagnostics, source/category comparisons, three figures and the English EDA section. See `results/data_audit.md`, `data/data_dictionary.md` and `docs/data_eda.md`. The source field `ISO3` maps explicitly to `country_iso3`. Source dates carry midnight UTC timestamps; historical publication availability and revision vintages remain unavailable.

The user confirmed Southeast Asian scope on 19 October: the core port panel retains all 10 coastal source countries, while Lao PDR remains outside this port forecast as specified by the repository plan. On 20 October, Han explicitly confirmed Dinh and Hieu's agreement to training 2019-2024, validation 2025 and test 2026-01-01 through 2026-10-02. These exact dates come from the conversation, not the supplied Word proposal, and are recorded in `experiment.json`.

Training-only candidate selection now produces `selected_ports.csv` with 137 IDs and fixed activity groups. The panel still contains all 210 source IDs. The separate validation-only sensitivity compares complete-coverage eligibility with the protocol's 20% activity candidate on common scoring keys. No test observations enter its features or labels. The sensitivity and candidate rules await joint Task 2 review before freezing; see `task1_handoff.md`.
