# Local data

Raw and derived panels are local and ignored by Git. Hân owns the data audit. The Task 1 branch uses the documented 18 October 2026 HDX download, covering 1 January 2019 to 2 October 2026. It contains 594,720 rows and 210 ports. Matching those counts does not prove byte identity with the separate 12 October snapshot described in the source attachments.

The introductions also mention older five-country repackaged data. Do not mix snapshots or assume their counts match the ten-country panel. Retrieve the existing group snapshot through the group’s original sharing channel, or obtain data from [IMF PortWatch](https://portwatch.imf.org/). Record the actual direct source and terms. The private group download link is not republished in this public repository.

## Handoff

- `ports_daily.csv`: cleaned panel following `data_dictionary.md`.
- `selected_ports.csv`: port ID, country, training coverage, active-day share, group and inclusion reason.
- `learning_table.csv`: Task 2 features, target, origin and split.
- Copy `manifest.example.csv` to `manifest.csv` and fill in provenance for each local file. Record the SHA-256 in `experiment.json` too.

Use a stable approved download location and record reproducible access steps before final submission. Check redistribution terms before publishing any data. Commit only reviewed provenance notes or small examples, not raw or derived panels. The local raw files and cleaned panel are not distributed in this repository.

## Local acquisition for Task 1

The Task 1 working branch includes `src/download_portwatch.py` for downloading public HDX CSV resources and verifying their hashes and original row inventory. `src/prepare_data.py --select-ports` produces the canonical panel, candidate list, dictionary-linked audit and EDA figures. See [data access](../docs/data_access.md), the [public provenance record](../docs/portwatch_snapshot_manifest.json) and [the handoff](../docs/task1_handoff.md). `selected_ports.csv` now contains 137 candidate IDs and training-defined activity groups using the agreed 2019-2024 period; the complete panel still contains all 210 IDs. The rule remains unfrozen pending joint review of the validation sensitivity. `learning_table.csv` belongs to Task 2. Neither raw nor derived panels should be committed to Git.
