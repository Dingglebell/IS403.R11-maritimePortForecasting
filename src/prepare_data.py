"""Task 1: verify a PortWatch snapshot, prepare the daily panel and audit zeros.

Port selection is a separate opt-in step requiring recorded agreement with
Task 2. No features, models, imputations or test scores are produced here.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd


SOURCE_MAP = {
    "date": "date", "portid": "port_id", "ISO3": "country_iso3",
    "import": "import_tonnes", "export": "export_tonnes", "portcalls": "portcalls",
}
MEASUREMENTS = ["import_tonnes", "export_tonnes", "portcalls", "cargo_tonnes"]
PANEL_COLUMNS = ["date", "port_id", "country_iso3", *MEASUREMENTS]
CORE_COUNTRIES = ["BRN", "IDN", "KHM", "MMR", "MYS", "PHL", "SGP", "THA", "TLS", "VNM"]
METHOD_SOURCE = "https://www.elibrary.imf.org/view/journals/001/2025/093/article-A001-en.xml"


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_csv(frame, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", na_rep="", lineterminator="\n")


def load_snapshot(manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("errors") or not manifest.get("files"):
        raise ValueError("The download manifest is incomplete or contains unresolved errors")
    records = sorted(manifest["files"], key=lambda r: r["country"])
    if len({r["country"] for r in records}) != len(records):
        raise ValueError("Repeated country resources in the snapshot manifest")
    frames = []
    for record in records:
        path = Path(record["file"])
        if not path.is_file():
            path = Path(manifest_path).parent / f"{record['country']}.csv"
        if sha256(path) != record["sha256"]:
            raise ValueError(f"Snapshot hash mismatch: {path}")
        frame = pd.read_csv(path, dtype={"portid": "string", "ISO3": "string"})
        frame["_source_country"] = record["country"]
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    bundle = "".join(f"{r['country']}.csv\t{r['sha256']}\n" for r in records)
    return raw, records, hashlib.sha256(bundle.encode("utf-8")).hexdigest()


def clean_daily_panel(raw):
    """Keep published totals and missing values; reject ambiguous/invalid keys."""
    missing = set(SOURCE_MAP) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required source columns: {sorted(missing)}")
    frame = raw[list(SOURCE_MAP)].rename(columns=SOURCE_MAP).copy()
    for column in ["port_id", "country_iso3"]:
        frame[column] = frame[column].astype("string").str.strip()
        if frame[column].isna().any() or frame[column].eq("").any():
            raise ValueError(f"Missing key field: {column}")
    if not frame["country_iso3"].str.fullmatch(r"[A-Z]{3}").all():
        raise ValueError("country_iso3 must contain uppercase ISO3 codes")
    timestamps = pd.to_datetime(frame["date"], format="ISO8601", utc=True, errors="raise")
    if timestamps.isna().any() or not timestamps.eq(timestamps.dt.normalize()).all():
        raise ValueError("Dates must be known midnight UTC source observations")
    frame["date"] = timestamps.dt.tz_localize(None)
    if frame.duplicated(["port_id", "date"]).any():
        raise ValueError("Duplicate (port_id,date) keys: investigate rather than silently deduplicating")
    country_counts = frame.groupby("port_id")["country_iso3"].nunique()
    if country_counts.gt(1).any():
        raise ValueError("A port_id maps to multiple countries; the shared key needs investigation")
    for column in ["import_tonnes", "export_tonnes", "portcalls"]:
        original = frame[column]
        frame[column] = pd.to_numeric(original, errors="coerce")
        if (original.notna() & frame[column].isna()).any():
            raise ValueError(f"Non-numeric measurement: {column}")
        known = frame[column].dropna()
        if not np.isfinite(known).all() or known.lt(0).any():
            raise ValueError(f"Negative or non-finite measurement: {column}")
    if frame["portcalls"].dropna().mod(1).ne(0).any():
        raise ValueError("Port-call counts must be whole nonnegative counts")
    # Arithmetic propagates missingness from either component; no fillna(0).
    frame["cargo_tonnes"] = frame["import_tonnes"] + frame["export_tonnes"]
    if not np.isfinite(frame["cargo_tonnes"].dropna()).all():
        raise ValueError("Non-finite derived cargo total")
    country_map = frame.groupby("port_id")["country_iso3"].first()
    calendar = pd.date_range(frame["date"].min(), frame["date"].max(), freq="D")
    complete_index = pd.MultiIndex.from_product(
        [sorted(country_map.index), calendar], names=["port_id", "date"]
    )
    indexed = frame.set_index(["port_id", "date"])
    absent = complete_index[~complete_index.isin(indexed.index)]
    gaps = absent.to_frame(index=False)
    gaps["country_iso3"] = gaps["port_id"].map(country_map)
    gaps["reason"] = "absent_source_record; measurements remain missing"
    panel = indexed.reindex(complete_index).reset_index()
    panel["country_iso3"] = panel["port_id"].map(country_map)
    return panel[PANEL_COLUMNS], gaps


def zero_runs(panel):
    ordered = panel.sort_values(["port_id", "date"]).copy()
    is_zero = ordered["cargo_tonnes"].eq(0)
    new_run = (ordered["port_id"].ne(ordered["port_id"].shift())
               | is_zero.ne(is_zero.shift(fill_value=False))
               | ordered["date"].diff().ne(pd.Timedelta(days=1)))
    ordered["_run"] = new_run.cumsum()
    ordered["_positive_calls"] = ordered["portcalls"].gt(0)
    ordered["_zero_calls"] = ordered["portcalls"].eq(0)
    ordered["_missing_calls"] = ordered["portcalls"].isna()
    result = ordered.loc[is_zero].groupby("_run", sort=True).agg(
        port_id=("port_id", "first"), country_iso3=("country_iso3", "first"),
        start_date=("date", "min"), end_date=("date", "max"), days=("date", "size"),
        days_with_positive_calls=("_positive_calls", "sum"), days_with_zero_calls=("_zero_calls", "sum"),
        days_with_missing_calls=("_missing_calls", "sum"), total_calls=("portcalls", "sum"),
    ).reset_index(drop=True)
    result["total_calls"] = result["total_calls"].astype(float)
    result.loc[result["days_with_missing_calls"].eq(result["days"]), "total_calls"] = np.nan
    result["touches_snapshot_start"] = result["start_date"].eq(panel["date"].min())
    result["touches_snapshot_end"] = result["end_date"].eq(panel["date"].max())
    return result


def summarize_panel(panel, runs):
    stats = panel.assign(
        known_cargo=panel["cargo_tonnes"].notna(),
        positive_cargo=panel["cargo_tonnes"].gt(0), zero_cargo=panel["cargo_tonnes"].eq(0),
        zero_with_calls=panel["cargo_tonnes"].eq(0) & panel["portcalls"].gt(0),
    ).groupby(["country_iso3", "port_id"], sort=True).agg(
        calendar_days=("date", "size"), known_cargo_days=("known_cargo", "sum"),
        active_days=("positive_cargo", "sum"), zero_days=("zero_cargo", "sum"),
        zero_days_with_calls=("zero_with_calls", "sum"), missing_call_days=("portcalls", lambda s: s.isna().sum()),
    ).reset_index()
    stats["cargo_coverage"] = stats["known_cargo_days"] / stats["calendar_days"]
    stats["active_share_observed"] = stats["active_days"] / stats["known_cargo_days"].replace(0, np.nan)
    stats["zero_share_observed"] = stats["zero_days"] / stats["known_cargo_days"].replace(0, np.nan)
    longest = runs.groupby("port_id")["days"].max() if len(runs) else pd.Series(dtype="int64")
    stats["longest_zero_run_days"] = stats["port_id"].map(longest).fillna(0).astype(int)
    countries = stats.groupby("country_iso3", sort=True).agg(
        ports=("port_id", "size"), calendar_rows=("calendar_days", "sum"),
        known_cargo_days=("known_cargo_days", "sum"), active_days=("active_days", "sum"),
        zero_days=("zero_days", "sum"), zero_days_with_calls=("zero_days_with_calls", "sum"),
    ).reset_index()
    countries["zero_share_observed"] = countries["zero_days"] / countries["known_cargo_days"].replace(0, np.nan)
    return stats, countries


def source_field_audit(raw):
    rows = []
    for column in raw.columns:
        if column.startswith("_"):
            continue
        is_numeric = column in ["year", "month", "day"] or column.startswith(("import", "export", "portcalls"))
        values = pd.to_numeric(raw[column], errors="coerce") if is_numeric else None
        rows.append({
            "source_field": column, "rows": len(raw), "missing_values": int(raw[column].isna().sum()),
            "invalid_numeric_values": int((raw[column].notna() & values.isna()).sum()) if is_numeric else 0,
            "negative_values": int(values.lt(0).sum()) if is_numeric else 0,
            "non_finite_values": int((values.notna() & ~np.isfinite(values)).sum()) if is_numeric else 0,
        })
    return pd.DataFrame(rows)


def component_audit(raw):
    result = []
    for total in ["portcalls", "import", "export"]:
        columns = [f"{total}_{category}" for category in ["container", "dry_bulk", "general_cargo", "roro", "tanker"]]
        if not set(columns).issubset(raw.columns):
            continue
        values = raw[[total, *columns]].apply(pd.to_numeric, errors="coerce")
        known = values.notna().all(axis=1)
        delta = values.loc[known, total] - values.loc[known, columns].sum(axis=1, min_count=len(columns))
        result.append({"source_total": total, "complete_rows": len(delta),
                       "different_from_category_sum": int(delta.ne(0).sum()),
                       "max_absolute_difference": float(delta.abs().max()) if len(delta) else None})
    return result


def select_ports(panel, experiment):
    """Eligibility and fixed activity bands use only the agreed training period."""
    agreement = experiment.get("time_split_agreement", {})
    if agreement.get("status") != "agreed" or not {"Dinh", "Hieu"}.issubset(agreement.get("agreed_by", [])):
        raise ValueError("Port selection requires recorded time-boundary agreement with Dinh and Hieu")
    fields = ["train_end", "validation_end", "test_end"]
    if any(not experiment.get(field) for field in fields):
        raise ValueError("All three agreed time boundaries are required before port selection")
    start = pd.Timestamp(experiment.get("train_start") or panel["date"].min())
    train_end, validation_end, test_end = [pd.Timestamp(experiment[field]) for field in fields]
    if not panel["date"].min() <= start <= train_end < validation_end < test_end <= panel["date"].max():
        raise ValueError("Boundaries must be chronological and inside snapshot coverage")
    rule = experiment.get("port_selection")
    if not isinstance(rule, dict) or rule.get("status") not in {"candidate_for_validation", "candidate_agreed_for_validation"}:
        raise ValueError("An explicit candidate rule is required; validation and final freezing belong to the joint handoff")
    if any(rule.get(field) is None for field in ["min_active_share", "min_cargo_coverage", "activity_group_cuts"]):
        raise ValueError("Fill the candidate activity threshold, coverage threshold and group cuts before selecting ports")
    threshold = float(rule["min_active_share"])
    coverage = float(rule["min_cargo_coverage"])
    cuts = rule["activity_group_cuts"]
    if len(cuts) != 2 or not 0 <= threshold <= 1 or not 0 < coverage <= 1 or not 0 < cuts[0] < cuts[1] < 1:
        raise ValueError("Invalid training-only eligibility thresholds or activity group cuts")
    days = (train_end - start).days + 1
    training = panel.loc[panel["date"].between(start, train_end)]
    ports = training.assign(known=training["cargo_tonnes"].notna(), active=training["cargo_tonnes"].gt(0)).groupby(
        ["port_id", "country_iso3"], sort=True
    ).agg(train_observed_cargo_days=("known", "sum"), train_active_days=("active", "sum")).reset_index()
    ports["train_calendar_days"] = days
    ports["train_coverage"] = ports["train_observed_cargo_days"] / days
    ports["train_active_share"] = ports["train_active_days"] / days
    ports["train_active_share_observed"] = ports["train_active_days"] / ports["train_observed_cargo_days"].replace(0, np.nan)
    ports["selected"] = ports["train_coverage"].ge(coverage) & ports["train_active_share"].ge(threshold)
    ports["reason"] = np.select(
        [ports["train_observed_cargo_days"].eq(0), ports["train_coverage"].lt(coverage), ports["train_active_share"].lt(threshold)],
        ["no_observed_training_cargo", "insufficient_training_coverage", "below_training_activity_threshold"],
        default="included_by_training_candidate",
    )
    ports["activity_group"] = pd.cut(ports["train_active_share"], [-np.inf, *cuts, np.inf], labels=["low", "medium", "high"], right=False).astype("string")
    ports.loc[~ports["selected"], "activity_group"] = pd.NA
    ports["rule_status"] = "candidate_pending_joint_validation; not_frozen"
    return ports


def make_figures(panel, ports, countries, results_dir):
    os.environ.setdefault("MPLCONFIGDIR", str((results_dir / ".matplotlib").resolve()))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 13, "text.color": "black",
                         "axes.labelcolor": "black", "axes.edgecolor": "black", "savefig.facecolor": "white"})
    figure_dir = results_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    monthly_records = []
    fig, axes = plt.subplots(5, 2, figsize=(12, 16), sharex=True, constrained_layout=True)
    for ax, (country, group) in zip(axes.flat, panel.groupby("country_iso3", sort=True)):
        n_ports = group["port_id"].nunique()
        daily = group.groupby("date")["cargo_tonnes"].sum(min_count=n_ports)
        monthly = daily.resample("MS").agg(["mean", "count"])
        ax.plot(monthly.index, monthly["mean"] / 1_000_000, color="black", linewidth=1)
        ax.set_title(f"{country}: {n_ports} ports")
        ax.set_ylabel("Million tonnes/day")
        ax.grid(axis="y", color="0.85", linewidth=0.6)
        for stamp, row in monthly.iterrows():
            monthly_records.append({"country_iso3": country, "month": stamp,
                                    "mean_daily_cargo_tonnes": row["mean"], "complete_days": int(row["count"])})
    fig.suptitle("Cargo history: monthly mean daily import + export\nFull-snapshot quality description; October 2026 contains two days", fontsize=15)
    fig.savefig(figure_dir / "cargo_history.png", dpi=170)
    plt.close(fig)
    write_csv(pd.DataFrame(monthly_records), results_dir / "monthly_cargo.csv")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    axes[0].hist(ports["active_share_observed"].dropna() * 100, bins=np.linspace(0, 100, 21), color="0.65", edgecolor="black")
    axes[0].set(xlabel="Positive-cargo share of observed days (%)", ylabel="Number of ports", title=f"All {len(ports)} ports; descriptive only")
    axes[1].bar(countries["country_iso3"], countries["zero_share_observed"] * 100, color="0.65", edgecolor="black")
    axes[1].set(xlabel="Country", ylabel="Zero-cargo share of observed days (%)", ylim=(0, 100), title="Observed zero days by country")
    axes[1].tick_params(axis="x", rotation=45)
    fig.suptitle("Activity rates across the full snapshot; not training-defined groups", fontsize=15)
    fig.savefig(figure_dir / "activity_rates.png", dpi=170)
    plt.close(fig)

    pairs = panel[["portcalls", "cargo_tonnes"]].dropna()
    fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True)
    if len(pairs):
        mesh = ax.hexbin(np.log1p(pairs["portcalls"]), np.log1p(pairs["cargo_tonnes"]), gridsize=55, mincnt=1, bins="log", cmap="Greys")
        fig.colorbar(mesh, ax=ax, label="Port-days per bin (log colour scale)")
    ax.set(xlabel="log(1 + daily port calls)", ylabel="log(1 + daily cargo in tonnes)",
           title=f"Cargo versus calls: {len(pairs):,} observed port-days\nZeros retained; association does not identify a cause")
    fig.savefig(figure_dir / "cargo_vs_calls.png", dpi=170)
    plt.close(fig)


def markdown_table(frame, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in frame[columns].itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_reports(audit, countries, runs, results_dir, eda_path):
    a = audit
    zero_pct = "NA" if a["zero_share_pct"] is None else f"{a['zero_share_pct']:.4f}"
    call_pct = "NA" if a["zero_with_positive_calls_pct_of_zeros"] is None else f"{a['zero_with_positive_calls_pct_of_zeros']:.2f}"
    reference_note = "The measured proportion rounds to the preliminary 54.2%." if a["zero_share_pct"] is not None and round(a["zero_share_pct"], 1) == 54.2 else "The preliminary 54.2% is not reproduced by this run."
    country_view = countries.copy()
    country_view["zero_pct"] = country_view["zero_share_observed"].map(lambda x: "NA" if pd.isna(x) else f"{100*x:.2f}")
    known_countries = countries.dropna(subset=["zero_share_observed"])
    if len(known_countries):
        min_zero = known_countries.loc[known_countries["zero_share_observed"].idxmin()]
        max_zero = known_countries.loc[known_countries["zero_share_observed"].idxmax()]
        heterogeneity = f"Observed zero-day shares range from {100*min_zero['zero_share_observed']:.2f}% in {min_zero['country_iso3']} to {100*max_zero['zero_share_observed']:.2f}% in {max_zero['country_iso3']}. The pooled zero rate masks substantial country heterogeneity; later evaluation should retain country and port breakdowns."
    else:
        heterogeneity = "Country zero-day shares are undefined because no cargo observations are known."
    table = markdown_table(country_view, ["country_iso3", "ports", "calendar_rows", "zero_days", "zero_pct", "zero_days_with_calls"])
    longest = runs.sort_values(["days", "port_id", "start_date"], ascending=[False, True, True]).head(10).copy()
    for col in ["start_date", "end_date"]:
        longest[col] = longest[col].dt.strftime("%Y-%m-%d")
    long_table = markdown_table(longest, ["port_id", "country_iso3", "start_date", "end_date", "days", "days_with_positive_calls"])
    if a["selection_run"]:
        s = a["port_selection"]
        retention = pd.DataFrame(s["country_retention"])
        selection = (
            f"The recorded time boundaries are training {s['train_start']} through {s['train_end']}, "
            f"validation {s['validation_start']} through {s['validation_end']}, and test "
            f"{s['test_start']} through {s['test_end']}. Han reported Dinh and Hieu's agreement on "
            "20 October 2026. The supplied Word proposal is not the source of these exact cutoffs.\n\n"
            f"The current candidate retains {s['selected_ports']} of {a['ports']} source IDs using only "
            f"{s['train_calendar_days']} training calendar days. It requires cargo coverage >= "
            f"{100*s['min_cargo_coverage']:g}% and a positive-cargo share >= {100*s['min_active_share']:g}%. "
            "Every excluded ID and reason is in `results/port_selection_audit.csv`. Observed zeros remain "
            "in all retained ports' histories and targets; no date is removed because it has zero cargo. "
            f"The fixed low/medium/high bands have lower-inclusive cuts at {s['activity_group_cuts']}; "
            f"group counts are {s['activity_groups']}. The bands are descriptive design choices applied to "
            "training shares, not thresholds fitted on future data.\n\n"
            + markdown_table(retention, ["country_iso3", "candidate_ports", "retained_ports", "excluded_ports"])
            + "\n\nCountry retention describes this candidate only. The rule remains unfrozen pending the "
            "joint Task 2 validation review. `results/eligibility_validation.md`, when generated by the "
            "documented validation command, records the independent sensitivity check for that review."
        )
    else:
        selection = "Port selection was not run; recorded time-boundary agreement and explicit candidate settings are required before running --select-ports."
    common = f"""The verified snapshot contains {a['raw_rows']:,} source rows for {a['ports']} port/terminal IDs in {a['countries']} coastal Southeast Asian countries. Source observations span {a['date_min']} to {a['date_max']} ({a['calendar_days']} calendar days). Local download date(s): {', '.join(a['download_dates_local'])}, independently of the group's reported 12 October copy. Matching preliminary counts does not establish byte identity. The SHA-256 bundle is `{a['data_snapshot_sha256']}`; its definition and individual file hashes are in `docs/portwatch_snapshot_manifest.json`.

The canonical panel has {a['panel_rows']:,} rows with unique `(port_id,date)` keys, sorted by port and date. The calendar check found {a['missing_calendar_records']:,} absent source records. Missing cargo measurements: {a['missing_cargo_days']:,}. Negative numeric source measurements: {a['negative_source_values']:,}. Invalid numeric source values: {a['invalid_numeric_source_values']:,}. No original row was deleted and no measurement was imputed, clipped or replaced. If another snapshot contains invalid keys, duplicate keys or invalid required measurements, preparation stops for investigation.

There are {a['zero_cargo_days']:,} observed zero-cargo days out of {a['known_cargo_days']:,} known cargo days ({zero_pct}%). {reference_note} The positive-cargo count is {a['positive_cargo_days']:,}. Missing cargo is outside this zero-rate denominator. On {a['zero_with_positive_calls']:,} zero-cargo days, port calls are positive ({call_pct}% of observed zeros). A reported zero is retained as an observed source value; it is not proof of no vessel activity or of a confirmed reporting gap.
"""
    report = f"""# Task 1 data audit

Audit generated at {a['generated_at_utc']}. Owner: Nguyen Thi Quynh Han. Status: panel and descriptive audit prepared; final eligibility decisions require joint validation review.

## Snapshot and canonical panel

{common}
Source mapping: `date -> date`, `portid -> port_id`, `ISO3 -> country_iso3`, `import -> import_tonnes`, `export -> export_tonnes`, and `portcalls -> portcalls`. Cargo is the sum of the two published aggregate shipment columns, in estimated metric tonnes. Category columns and subtotals are not added again. UTC midnight source labels are retained as calendar dates without a conversion to local dates. Detailed mappings and missingness rules are in `data/data_dictionary.md`.

## Country coverage and zeros

{table}

These are full-snapshot descriptive counts, not training-based eligibility or retention. All source countries and ports are retained in the clean panel. Candidate country retention, when selection is run, is reported in the handoff section below.

{heterogeneity}

## Long zero runs and possible gaps

Observed zero runs: {a['zero_runs']:,}. Runs lasting at least 28 days: {a['long_zero_runs']:,}, involving {a['ports_with_long_zero_runs']} ports. Of those long runs, {a['long_zero_runs_with_calls']:,} contain at least one positive-call day. The 28-day flag is a diagnostic matching the proposed four-week feature history, not a port exclusion rule. Entire-snapshot zero-cargo ports: {a['entire_snapshot_zero_ports']}. Missing days and missing measurements break a zero run.

Retaining zeros matters for the study target: the next seven calendar days must include observed zero days. Dropping them would compress the calendar, change the forecast horizon and train only on a conditional positive-activity sample. Missing observations instead make the corresponding complete-window sample unavailable under the protocol. This preparation neither deletes zeros nor substitutes a zero for an unknown observation.

The ten longest runs are shown below. Runs touching a snapshot boundary are censored: their recorded durations cover only the observed segment. Boundary flags are retained in the run table. A long run with calls is a priority for source review; the aggregate fields alone cannot distinguish genuinely small/zero estimated shipments, estimation limitations and AIS/reporting gaps. No run has been relabelled missing, deleted or declared erroneous without independent evidence. Full run diagnostics are in `zero_runs.csv`; the >=28-day subset is in `long_zero_runs.csv`.

Source names explicitly label {a['source_named_offshore_oil_terminal_ids']} of the {a['ports']} IDs as Offshore Oil Terminals. They account for {a['all_zero_source_named_offshore_ids']} of the {a['entire_snapshot_zero_ports']} entire-snapshot zero-cargo IDs. Other entire-snapshot zero IDs and source names: {a['other_all_zero_source_names']}. This is a source-metadata classification, not an independently validated asset taxonomy or an explanation of AIS/volume estimation failures. The descriptive coverage by source label is saved in `entity_coverage.csv`. No source-label or full-snapshot-zero filter is applied to select modelling ports.

{long_table}

## Aggregate and category consistency

{markdown_table(pd.DataFrame(a['component_checks']), ['source_total', 'complete_rows', 'different_from_category_sum', 'max_absolute_difference'])}

Small shipment differences are compatible with independently rounded or truncated estimates, but the exact mechanism is not established. Published aggregate import/export values remain authoritative for this study. No repair is made by adding a subtotal and its components together. Port-call totals are checked against the five disjoint source ship categories.

## Figures

![Country cargo history](figures/cargo_history.png)

Monthly mean daily cargo is computed from complete country-day totals. October 2026 has only two observed days and must not be compared as a full monthly total.

![Descriptive activity rates](figures/activity_rates.png)

Activity rates here describe data quality and heterogeneity. They do not assign low/medium/high model groups; those groups must use training observations only.

![Cargo versus calls](figures/cargo_vs_calls.png)

All complete cargo/call pairs are included in log-transformed density bins. This plot retains zeros and does not establish a causal relation between vessel calls and estimated cargo.

## Exclusions and handoff

No source row or port is excluded from preparation. Non-canonical source columns remain in the immutable raw CSVs; port names are retained in `data/ports_metadata.csv`. No national trade, weather or oil series is joined. Lao PDR has no port series in the core panel, as specified by the repository scope.

{selection}

The supplied proposal describes PortWatch trends over 2019-2026 and 2019-2024 for auxiliary national trade data; it gives no explicit train/validation/test cutoffs. The repository requires agreement with Dinh and Hieu before selecting ports. A 20% active-day threshold remains a candidate. Compare candidate eligibility rules jointly with Task 2 on validation MAE and an unchanged intersection of valid port-origin keys; retain zeros in every candidate. Do not compare scores from different evaluation populations or use test results to choose a rule. This preparation report contains no validation or test scores; the separate validation-only diagnostic supports the joint review.

## Availability and interpretation limits

The local HDX metadata identifies weekly updates; this snapshot ends {a['download_gap_calendar_days']} calendar days before its earliest local download date. That observed snapshot gap is not a verified historical release lag. Origin-level publication timestamps and revision vintages are unavailable, so same-day availability through t is not established. Task 2 must record an information-cutoff convention before claiming an operational backtest. Historical revised data can be optimistic relative to data available in real time.

IMF describes AIS-derived shipments as estimates and notes that source-data updates, methodology changes and coverage changes can cause revisions ([IMF Working Paper 25/93, section 2]({METHOD_SOURCE})). Cargo is neither revenue nor measured terminal capacity. Forecasts may inform resource planning; congestion, utilisation or savings need independent operational evidence.

## Reproduction

Run the preparation command documented in the root README. The audit JSON records package versions, the preparation-script hash, snapshot hash and output-panel hash. Raw files and derived panels remain ignored by Git. Review small result tables and figures explicitly before adding them to a pull request.
"""
    (results_dir / "data_audit.md").write_text(report, encoding="utf-8", newline="\n")
    eda = f"""# Data and Exploratory Analysis

## Data provenance and scope

{common}
The core task forecasts total estimated cargo during the seven calendar days after each origin, with daily cargo defined as published import plus export. The acquisition covers Brunei Darussalam, Cambodia, Indonesia, Malaysia, Myanmar, the Philippines, Singapore, Thailand, Timor-Leste and Viet Nam. Lao PDR belongs to national trade/transit analysis in the broader proposal and is outside the repository's core port forecast. The older five-country repackaged data are not mixed into this snapshot.

## Preparation and measurement

Preparation verifies every raw file hash, validates date and port keys, checks numeric values, and reindexes each port over a common daily calendar. Published midnight UTC observation labels become ISO calendar dates. Unknown measurements remain missing; cargo is unknown if either import or export is unknown. The full source schema has 29 fields. The shared panel contains exactly the seven agreed columns, and source names and cleaning rules are retained in the dictionary. Port names are metadata rather than identifiers. Aggregate shipment estimates are used directly to avoid double-counting category subtotals.

## Zero days and activity heterogeneity

Country coverage and observed zero frequencies are shown below.

{table}

{heterogeneity}

There are {a['long_zero_runs']:,} zero runs lasting at least 28 days, across {a['ports_with_long_zero_runs']} ports; {a['long_zero_runs_with_calls']:,} of these runs include positive port calls. Such patterns warrant source review but do not by themselves establish missing records, port closure or data errors. All observed zeros are retained. A future imputation or eligibility sensitivity must be justified and evaluated on validation without changing the scoring rows.

The source entity coverage is broader than conventional port names alone: {a['source_named_offshore_oil_terminal_ids']} IDs carry source names containing Offshore Oil Terminal. Of the {a['entire_snapshot_zero_ports']} entire-snapshot zero-cargo entities, {a['all_zero_source_named_offshore_ids']} are source-labelled offshore oil terminals; the audit identifies any remaining source IDs/names explicitly. This metadata pattern motivates source review and careful interpretation, not an automatic exclusion or a claim that all zero estimates are reporting gaps.

Observed zeros must remain in both the history and seven-calendar-day target. Deleting zero days would compress time, change the horizon and condition the sample on positive activity. Unknown cargo is a different case: it prevents construction of a complete feature/target window under the shared protocol and must not be replaced with zero by default.

![Cargo history](../results/figures/cargo_history.png)

The country histories show monthly means of daily estimated cargo; they describe all available observations, including the two-day October 2026 endpoint. They are not forecasts or comparisons of full monthly totals.

![Activity rates](../results/figures/activity_rates.png)

The full-snapshot activity distribution motivates analysis of sparse activity. It is descriptive and is not reused as training-defined eligibility or as an activity group assignment.

![Cargo and calls](../results/figures/cargo_vs_calls.png)

Cargo and calls are different measures. The presence of calls on {a['zero_with_positive_calls']:,} zero-cargo days demonstrates why zero estimated volume should not automatically be interpreted as no vessel activity. This association does not identify the cause of the estimated volume.

## Training-only eligibility and validation handoff

{selection}

The implementation records both the calendar-day denominator and the observed-cargo denominator, exclusion reasons and retention by country. No full-sample count, including an earlier claim of 138 ports, is treated as a training-only finding. The exact dates are recorded from the user's confirmation of team agreement, not inferred from auxiliary trade-data coverage.

Task 2 owns the production learning table and baseline comparisons. A separate Task 1 sensitivity check can exercise the shared protocol for joint review without replacing Task 2's deliverables. Candidate rules must share valid evaluation origins and complete feature/target windows, with labels entirely inside their assigned periods. Selection, grouping and any preprocessing use training observations only. Validation MAE is the primary selection criterion; test scoring is reserved until choices are frozen. Final joint review remains pending; this descriptive section contains no modelling results.

## Availability and application limits

The snapshot has no origin-level publication timestamps or historical release vintages. Its latest observation predates the earliest local download by {a['download_gap_calendar_days']} calendar days; this is not a measured historical release schedule. Same-day observation availability must be verified or an explicitly lagged information cutoff adopted for the backtest. Source revisions and AIS coverage limitations prevent treating the panel as error-free operational ground truth. The IMF documents revision channels and the estimated nature of these indicators ([IMF Working Paper 25/93, section 2]({METHOD_SOURCE})). Estimated cargo supports discussion of operational demand; measured capacity, congestion and financial savings require separate evidence.

Detailed field checks, source hashes, component discrepancies, run-level diagnostics and exclusions are available in `results/data_audit.md`, `results/data_audit.json` and the data dictionary. No independent reporting-gap explanation has been fabricated.
"""
    Path(eda_path).parent.mkdir(parents=True, exist_ok=True)
    Path(eda_path).write_text(eda, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--eda-doc", type=Path, default=Path("docs/data_eda.md"))
    parser.add_argument("--select-ports", action="store_true")
    args = parser.parse_args()
    experiment = json.loads(args.experiment.read_text(encoding="utf-8"))
    raw, records, bundle_hash = load_snapshot(args.snapshot)
    if experiment.get("data_snapshot_sha256") not in [None, bundle_hash]:
        raise ValueError("This snapshot differs from experiment.json; resolve provenance before replacing the experiment dataset")
    fields = source_field_audit(raw)
    if fields[["negative_values", "invalid_numeric_values", "non_finite_values"]].to_numpy().sum():
        args.results_dir.mkdir(parents=True, exist_ok=True)
        write_csv(fields, args.results_dir / "source_field_audit.csv")
        raise ValueError("Invalid source numeric values; inspect source_field_audit.csv before continuing")
    panel, gaps = clean_daily_panel(raw)
    if set(panel["country_iso3"]) != set(CORE_COUNTRIES):
        raise ValueError("Snapshot country coverage differs from the agreed Southeast Asian coastal acquisition scope")
    dates = pd.to_datetime(raw["date"], format="ISO8601", utc=True)
    date_component_errors = {col: int(pd.to_numeric(raw[col], errors="coerce").ne(getattr(dates.dt, col)).sum())
                             for col in ["year", "month", "day"] if col in raw}
    if any(date_component_errors.values()):
        raise ValueError(f"Source calendar columns disagree with date: {date_component_errors}")
    selection = select_ports(panel, experiment) if args.select_ports else None
    if selection is None and (args.output_dir / "selected_ports.csv").exists():
        raise ValueError("A selected_ports.csv already exists; do not silently leave it stale during an audit-only run")
    runs = zero_runs(panel)
    ports, countries = summarize_panel(panel, runs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.results_dir.mkdir(parents=True, exist_ok=True)
    write_csv(panel, args.output_dir / "ports_daily.csv")
    write_csv(gaps, args.results_dir / "missing_calendar_dates.csv")
    write_csv(fields, args.results_dir / "source_field_audit.csv")
    write_csv(ports, args.results_dir / "port_audit.csv")
    write_csv(countries, args.results_dir / "country_audit.csv")
    write_csv(runs, args.results_dir / "zero_runs.csv")
    long_runs = runs.loc[runs["days"].ge(28)]
    write_csv(long_runs, args.results_dir / "long_zero_runs.csv")
    metadata = raw.groupby(["portid", "ISO3"], sort=True).agg(
        source_port_names=("portname", lambda s: " | ".join(sorted(s.dropna().unique()))),
        source_country_names=("country", lambda s: " | ".join(sorted(s.dropna().unique()))),
    ).reset_index().rename(columns={"portid": "port_id", "ISO3": "country_iso3"})
    metadata["source_named_offshore_oil_terminal"] = metadata["source_port_names"].str.contains("Offshore Oil Terminal", case=False, regex=False)
    write_csv(metadata, args.output_dir / "ports_metadata.csv")
    entity_stats = ports.merge(metadata, on=["port_id", "country_iso3"], validate="one_to_one")
    entity_coverage = entity_stats.groupby("source_named_offshore_oil_terminal", sort=True).agg(
        source_ids=("port_id", "size"), calendar_rows=("calendar_days", "sum"), known_cargo_days=("known_cargo_days", "sum"),
        zero_days=("zero_days", "sum"), zero_days_with_calls=("zero_days_with_calls", "sum"),
    ).reset_index()
    entity_coverage["zero_share_observed"] = entity_coverage["zero_days"] / entity_coverage["known_cargo_days"].replace(0, np.nan)
    write_csv(entity_coverage, args.results_dir / "entity_coverage.csv")
    if selection is not None:
        write_csv(selection.loc[selection["selected"]], args.output_dir / "selected_ports.csv")
        write_csv(selection, args.results_dir / "port_selection_audit.csv")
        retention = selection.groupby("country_iso3").agg(candidate_ports=("port_id", "size"), retained_ports=("selected", "sum")).reset_index()
        retention["excluded_ports"] = retention["candidate_ports"] - retention["retained_ports"]
        write_csv(retention, args.results_dir / "country_retention.csv")
        write_json(args.results_dir / "port_selection_rules.json", {
            "train_start": experiment.get("train_start", panel["date"].min().strftime("%Y-%m-%d")),
            "train_end": experiment["train_end"], "validation_end": experiment["validation_end"],
            "test_end": experiment["test_end"], "rule": experiment["port_selection"],
            "snapshot_sha256": bundle_hash, "frozen": False,
            "time_split_agreement": experiment["time_split_agreement"],
            "remaining": "Review validation-only sensitivity with Task 2 and jointly freeze the chosen rule before test scoring",
        })
    known = panel["cargo_tonnes"].notna()
    zeros = panel["cargo_tonnes"].eq(0)
    zero_calls = zeros & panel["portcalls"].gt(0)
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "panel_and_eda_prepared; joint_selection_and_validation_pending",
        "raw_rows": len(raw), "panel_rows": len(panel), "ports": int(panel["port_id"].nunique()),
        "countries": int(panel["country_iso3"].nunique()), "calendar_days": int(panel["date"].nunique()),
        "date_min": panel["date"].min().strftime("%Y-%m-%d"), "date_max": panel["date"].max().strftime("%Y-%m-%d"),
        "missing_calendar_records": len(gaps), "missing_cargo_days": int((~known).sum()),
        "duplicate_port_date_keys": int(raw.duplicated(["portid", "date"]).sum()),
        "missing_source_values": int(fields["missing_values"].sum()),
        "negative_source_values": int(fields["negative_values"].sum()),
        "invalid_numeric_source_values": int(fields["invalid_numeric_values"].sum()),
        "source_calendar_component_errors": date_component_errors,
        "known_cargo_days": int(known.sum()), "positive_cargo_days": int(panel["cargo_tonnes"].gt(0).sum()),
        "zero_cargo_days": int(zeros.sum()), "zero_share_pct": float(100 * zeros.sum() / known.sum()) if known.any() else None,
        "zero_with_positive_calls": int(zero_calls.sum()),
        "zero_with_positive_calls_pct_of_zeros": float(100 * zero_calls.sum() / zeros.sum()) if zeros.any() else None,
        "positive_cargo_without_calls": int((panel["cargo_tonnes"].gt(0) & panel["portcalls"].eq(0)).sum()),
        "zero_runs": len(runs), "long_zero_runs": len(long_runs),
        "ports_with_long_zero_runs": int(long_runs["port_id"].nunique()),
        "long_zero_runs_with_calls": int(long_runs["days_with_positive_calls"].gt(0).sum()),
        "entire_snapshot_zero_ports": int(ports["zero_days"].eq(ports["calendar_days"]).sum()),
        "source_named_offshore_oil_terminal_ids": int(metadata["source_named_offshore_oil_terminal"].sum()),
        "all_zero_source_named_offshore_ids": int((entity_stats["source_named_offshore_oil_terminal"] & entity_stats["zero_days"].eq(entity_stats["calendar_days"])).sum()),
        "other_all_zero_source_names": "; ".join(entity_stats.loc[~entity_stats["source_named_offshore_oil_terminal"] & entity_stats["zero_days"].eq(entity_stats["calendar_days"])].apply(lambda r: f"{r['port_id']} ({r['source_port_names']})", axis=1)) or "none",
        "longest_zero_run_days": int(runs["days"].max()) if len(runs) else 0,
        "source_rows_excluded": 0, "ports_excluded_from_panel": 0, "imputed_measurements": 0,
        "component_checks": component_audit(raw), "selection_run": selection is not None,
        "data_snapshot_sha256": bundle_hash, "panel_sha256": sha256(args.output_dir / "ports_daily.csv"),
        "preparation_script_sha256": sha256(__file__),
        "versions": {name: importlib.metadata.version(name) for name in ["pandas", "numpy", "matplotlib"]},
        "python": platform.python_version(), "source_files": [{k: r[k] for k in ["country", "source_url", "sha256"]} for r in records],
    }
    audit["download_dates_local"] = sorted({datetime.fromisoformat(r.get("downloaded_at_utc") or r["local_file_mtime_utc"]).astimezone(timezone(timedelta(hours=7))).date().isoformat() for r in records})
    audit["download_gap_calendar_days"] = (pd.Timestamp(audit["download_dates_local"][0]) - panel["date"].max()).days
    if selection is not None:
        rule = experiment["port_selection"]
        audit["status"] = "panel_eda_and_candidate_ports_prepared; joint_validation_review_pending"
        audit["port_selection"] = {
            **{k: experiment[k] for k in ["train_start", "train_end", "validation_end", "test_end"]},
            "validation_start": (pd.Timestamp(experiment["train_end"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "test_start": (pd.Timestamp(experiment["validation_end"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            "train_calendar_days": int(selection["train_calendar_days"].iloc[0]),
            "selected_ports": int(selection["selected"].sum()),
            "activity_groups": {str(k): int(v) for k, v in selection.loc[selection["selected"], "activity_group"].value_counts().sort_index().items()},
            "country_retention": retention.to_dict("records"),
            **{k: rule[k] for k in ["min_active_share", "min_cargo_coverage", "activity_group_cuts"]},
            "frozen": False,
        }
    make_figures(panel, ports, countries, args.results_dir)
    write_json(args.results_dir / "data_audit.json", audit)
    write_reports(audit, countries, runs, args.results_dir, args.eda_doc)
    experiment["data_snapshot_sha256"] = bundle_hash
    experiment["data_snapshot_hash_definition"] = "SHA-256 of UTF-8 country-slug.csv<TAB>file-sha256<LF> lines sorted by country slug"
    experiment["country_scope_iso3"] = CORE_COUNTRIES
    experiment["status"] = "task1_candidate_ports_prepared; joint_validation_review_pending" if selection is not None else "task1_panel_audited; selection_not_run"
    write_json(args.experiment, experiment)
    print(json.dumps({key: audit[key] for key in ["panel_rows", "ports", "zero_cargo_days", "zero_share_pct", "missing_calendar_records", "long_zero_runs", "selection_run", "status"]}, indent=2))


if __name__ == "__main__":
    main()
