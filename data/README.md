# Local data

Hân's verified local snapshot is in `raw/hdx_2026-10-18/`: ten country CSVs and the original provenance metadata. It covers 1 January 2019 to 2 October 2026, with 594,720 rows and 210 port/terminal IDs. It was obtained/verified on 18 October; identity with the group's earlier 12 October copy is unverified. Raw files are ignored by Git and remain unchanged.

The introductions also mention older five-country repackaged data. Do not mix snapshots or assume their counts match the ten-country panel. Retrieve the existing group snapshot through the group’s original sharing channel, or obtain data from [IMF PortWatch](https://portwatch.imf.org/). Record the actual direct source and terms. The private group download link is not republished in this public repository.

## Handoff

- `ports_daily.csv`: cleaned panel following `data_dictionary.md`.
- `selected_ports.csv`: port ID, country, training coverage, active-day share, group and inclusion reason.
- `learning_table.csv`: Task 2 features, target, origin and split.
- `ports_metadata.csv`: source port/country names and descriptive offshore-name flag.
- `source_manifest.csv`: verified per-file hashes, dates and stable source URLs. The bundle hash is in `experiment.json`; temporary signed download redirects are excluded.

For an exact rerun, obtain the unchanged local snapshot through the group's agreed sharing channel, keeping the original `snapshot.json` beside the ten CSVs. Run the commands in the root README. The source manifest links each public HDX page and resource; current downloads may be revised and must match the recorded hashes for this experiment. A newer snapshot requires a separate documented rerun, not silent substitution. Source terms are recorded per file. Commit only reviewed provenance notes or small examples, not raw or derived panels. The selected list contains 210 recommended IDs plus the alternative 20% eligibility flag; it remains subject to joint Task 2 review.
