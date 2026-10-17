# Canonical daily panel

This is the target schema to produce after inspecting the source, not a claim about the source’s exact field spellings.

| Field | Type | Meaning |
|---|---|---|
| date | YYYY-MM-DD | Observation day; document time convention |
| port_id | string | Stable source port or terminal identifier |
| country_iso3 | string | Country code from source |
| import_tonnes | numeric | Estimated inbound cargo in tonnes |
| export_tonnes | numeric | Estimated outbound cargo in tonnes |
| portcalls | numeric | Daily port calls; document included ship categories |
| cargo_tonnes | numeric | import_tonnes + export_tonnes; missing if either is unknown |

Unique key: port_id plus date. Record field mappings, units, source definitions and cleaning rules after the audit. Keep zero values distinct from missing values. Verify nonnegative measurements and do not sum incompatible cargo or ship-category columns twice.
