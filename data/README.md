# Local data

Put the exact downloaded PortWatch snapshot here locally; raw files are ignored by Git. Hân owns the data audit. The source attachments describe a 12 October 2026 snapshot covering 1 January 2019 to 2 October 2026, but the dataset has not been supplied in this workspace or independently checked here.

The introductions also mention older five-country repackaged data. Do not mix snapshots or assume their counts match the ten-country panel. Retrieve the existing group snapshot through the group’s original sharing channel, or obtain data from [IMF PortWatch](https://portwatch.imf.org/). Record the actual direct source and terms. The private group download link is not republished in this public repository.

## Handoff

- `ports_daily.csv`: cleaned panel following `data_dictionary.md`.
- `selected_ports.csv`: port ID, country, training coverage, active-day share, group and inclusion reason.
- `learning_table.csv`: Task 2 features, target, origin and split.
- Copy `manifest.example.csv` to `manifest.csv` and fill in provenance for each local file. Record the SHA-256 in `experiment.json` too.

Use a stable approved download location and record reproducible access steps before final submission. Check redistribution terms before publishing any data. Commit only reviewed provenance notes or small examples, not raw or derived panels. This repository currently has no dataset.
