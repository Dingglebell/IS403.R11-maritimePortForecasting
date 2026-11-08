"""Independently review Task 2 features, labels, training eligibility and boundaries.

Run features.py first. This checker uses cumulative sums, not its rolling-window
implementation. It reviews the frozen snapshot and never fits a model.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from features import FEATURES, KEYS, read_panel, sha256, validate_config


def interval_sums(values, starts, ends):
    """Sum half-open array intervals; unknown or incomplete intervals yield NaN."""
    values = np.asarray(values, dtype=float)
    known = np.isfinite(values)
    totals = np.r_[0., np.cumsum(np.where(known, values, 0.))]
    counts = np.r_[0, np.cumsum(known)]
    left, right = np.clip(starts, 0, len(values)), np.clip(ends, 0, len(values))
    complete = (starts >= 0) & (ends <= len(values)) & (counts[right] - counts[left] == ends - starts)
    return np.where(complete, totals[right] - totals[left], np.nan)


def independent_windows(panel, config):
    """Reconstruct all complete rows and exclusions directly from daily arrays."""
    start, a, b = validate_config(config)
    history = panel.loc[panel.date.between(start, b)].sort_values(["port_id", "date"])
    calendar = pd.date_range(start, b)
    train_days = len(pd.date_range(start, a))
    tables, exclusions, selections = [], [], []
    for pid, g in history.groupby("port_id", sort=True):
        g = g.reset_index(drop=True)
        if not np.array_equal(g.date.to_numpy(), calendar.to_numpy()):
            raise ValueError(f"{pid}: daily calendar differs from the frozen review period")
        cargo = g.cargo_tonnes.to_numpy(float)
        calls = g.portcalls.to_numpy(float)
        training = g.date.le(a).to_numpy()
        known_cargo = np.isfinite(cargo[training]).sum()
        known_calls = np.isfinite(calls[training]).sum()
        active_days = (cargo[training] > 0).sum()
        selected = known_cargo == train_days and known_calls == train_days
        share = active_days / train_days
        lo, hi = config["port_selection"]["activity_group_cuts"]
        activity = "low" if share < lo else "medium" if share < hi else "high"
        selections.append({"port_id": pid, "train_known_days": known_cargo,
            "train_calls_known_days": known_calls, "train_active_days": active_days,
            "train_calendar_days": train_days, "train_active_share": share,
            "selected": selected, "activity_group": activity,
            "candidate_active20": selected and share >= config["port_selection"]["candidate_active_share"]})
        i = np.arange(len(g))
        f = g[["port_id", "country_iso3", "date"]].rename(columns={"date": "origin_date"}).copy()
        f["cargo_7d"] = interval_sums(cargo, i - 6, i + 1)
        f["calls_7d"] = interval_sums(calls, i - 6, i + 1)
        f["cargo_mean_28d"] = interval_sums(cargo, i - 27, i + 1) / 28
        f["target_7d"] = interval_sums(cargo, i + 1, i + 8)
        f["target_start"] = f.origin_date + pd.Timedelta(days=1)
        f["target_end"] = f.origin_date + pd.Timedelta(days=7)
        f["split"] = "excluded"
        f.loc[f.target_end.le(a), "split"] = "train"
        f.loc[f.origin_date.ge(a) & f.target_end.le(b), "split"] = "validation"
        reason = pd.Series("", index=f.index)
        reason.loc[f.target_7d.isna()] = "incomplete_target"
        reason.loc[f[FEATURES].isna().any(axis=1)] = "incomplete_history"
        reason.loc[f.split.eq("excluded")] = "target_crosses_train_boundary"
        reason.loc[f.target_end.gt(b)] = "target_beyond_validation"
        if not selected:
            reason[:] = "incomplete_training_port_coverage"
        f["exclusion_reason"] = reason
        f["activity_group"] = activity
        tables.append(f.loc[reason.eq("")].drop(columns="exclusion_reason"))
        exclusions.append(f.loc[reason.ne(""), [*KEYS, "split", "exclusion_reason"]])
    if not tables:
        raise ValueError("No daily series in the review period")
    return pd.concat(tables, ignore_index=True), pd.DataFrame(selections), pd.concat(exclusions, ignore_index=True)


def compare_table(actual, expected):
    actual = actual.sort_values(KEYS).reset_index(drop=True)
    expected = expected.sort_values(KEYS).reset_index(drop=True)
    if actual.duplicated(KEYS).any() or len(actual) != len(expected):
        raise ValueError("Learning-table row count or key uniqueness differs")
    checks = []
    for column in [*KEYS, "country_iso3", "activity_group", "target_start", "target_end", "split"]:
        if not actual[column].eq(expected[column]).all():
            raise ValueError(f"Independent reconstruction differs: {column}")
        checks.append({"check": column, "rows_checked": len(actual), "passed": True, "max_abs_error": 0.})
    for column in [*FEATURES, "target_7d"]:
        np.testing.assert_allclose(actual[column], expected[column], rtol=0, atol=1e-8, err_msg=column)
        checks.append({"check": column, "rows_checked": len(actual), "passed": True,
                       "max_abs_error": float((actual[column] - expected[column]).abs().max())})
    return pd.DataFrame(checks)


def review_features(panel, table, ports, excluded, config, example_port, example_origin):
    expected, selection, expected_excluded = independent_windows(panel, config)
    checks = compare_table(table, expected)
    columns = list(selection.columns)
    pd.testing.assert_frame_equal(ports[columns].sort_values("port_id").reset_index(drop=True),
        selection.sort_values("port_id").reset_index(drop=True), check_dtype=False, rtol=0, atol=1e-12)
    pd.testing.assert_frame_equal(excluded.sort_values(KEYS).reset_index(drop=True),
        expected_excluded.sort_values(KEYS).reset_index(drop=True), check_dtype=False)
    t = pd.Timestamp(example_origin)
    example = table.loc[table.port_id.eq(example_port) & table.origin_date.eq(t)]
    if len(example) != 1:
        raise ValueError("Choose a complete port/origin row for the hand check")
    daily = panel.loc[panel.port_id.eq(example_port) & panel.date.between(t-pd.Timedelta(days=27), t+pd.Timedelta(days=7))].copy()
    if len(daily) != 35:
        raise ValueError("Hand check requires all 35 calendar days")
    daily = daily.sort_values("date")
    daily["cargo_7d_input"] = daily.date.between(t-pd.Timedelta(days=6), t)
    daily["cargo_28d_input"] = daily.date.le(t)
    daily["target_input"] = daily.date.gt(t)
    cargo7 = daily.loc[daily.cargo_7d_input, "cargo_tonnes"].sum(min_count=7)
    calls7 = daily.loc[daily.cargo_7d_input, "portcalls"].sum(min_count=7)
    cargo28 = daily.loc[daily.cargo_28d_input, "cargo_tonnes"].sum(min_count=28)
    target = daily.loc[daily.target_input, "cargo_tonnes"].sum(min_count=7)
    summary = pd.DataFrame([{"port_id": example_port, "origin_date": t,
        "history_7d_start": t-pd.Timedelta(days=6), "history_28d_start": t-pd.Timedelta(days=27),
        "target_start": t+pd.Timedelta(days=1), "target_end": t+pd.Timedelta(days=7),
        "cargo_7d": cargo7, "calls_7d": calls7, "cargo_28d_sum": cargo28,
        "cargo_mean_28d": cargo28 / 28, "target_7d": target, "split": example.split.iloc[0]}])
    np.testing.assert_allclose(summary[[*FEATURES, "target_7d"]], example[[*FEATURES, "target_7d"]], rtol=0, atol=1e-8)
    # Show the first complete history and both chronological boundaries for this port.
    a, b = pd.Timestamp(config["train_end"]), pd.Timestamp(config["validation_end"])
    first = pd.Timestamp(config["train_start"]) + pd.Timedelta(days=27)
    candidates = set(pd.date_range(a-pd.Timedelta(days=7), a)) | set(pd.date_range(b-pd.Timedelta(days=7), b)) | {first-pd.Timedelta(days=1), first}
    kept = table.loc[table.port_id.eq(example_port) & table.origin_date.isin(candidates),
                     [*KEYS, "target_start", "target_end", "split"]].copy()
    kept["decision"] = "keep"
    omitted = excluded.loc[excluded.port_id.eq(example_port) & excluded.origin_date.isin(candidates)].copy()
    omitted["target_start"] = omitted.origin_date + pd.Timedelta(days=1)
    omitted["target_end"] = omitted.origin_date + pd.Timedelta(days=7)
    omitted = omitted.rename(columns={"exclusion_reason": "decision"})
    boundary = pd.concat([kept, omitted], ignore_index=True).sort_values("origin_date")
    return checks, summary, daily, boundary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--panel", type=Path, default=Path("data/da_xu_ly/ports_daily.csv"))
    p.add_argument("--table", type=Path, default=Path("data/learning_table.csv"))
    p.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    p.add_argument("--results-dir", type=Path, default=Path("results"))
    p.add_argument("--daily-output", type=Path, default=Path("data/task2_handcheck_daily.csv"))
    p.add_argument("--example-port", default="port434", help="Default is Hai Phong")
    a = p.parse_args()
    config = json.loads(a.experiment.read_text(encoding="utf-8"))
    panel = read_panel(a.panel)
    task1_record = json.loads(Path("results/task1_run.json").read_text(encoding="utf-8"))
    expected_hash = task1_record["panel_sha256"]
    if sha256(a.panel) != expected_hash:
        p.error("This review requires Task 1's frozen clean-panel hash")
    table = pd.read_csv(a.table, parse_dates=["origin_date", "target_start", "target_end"], dtype={"port_id": "string"})
    ports = pd.read_csv(a.results_dir / "task2_ports.csv", dtype={"port_id": "string"})
    excluded = pd.read_csv(a.results_dir / "task2_window_exclusions.csv", parse_dates=["origin_date"], dtype={"port_id": "string"})
    checks, summary, daily, boundary = review_features(panel, table, ports, excluded, config, a.example_port, config["train_end"])
    keys = table.loc[table.split.eq("validation"), [*KEYS, "target_start", "target_end"]].sort_values(KEYS)
    key_hash = hashlib.sha256(keys.to_csv(index=False, date_format="%Y-%m-%d", lineterminator="\n").encode()).hexdigest()
    if key_hash != task1_record["validation_keys_sha256"]:
        p.error("Validation keys differ from Task 1's frozen comparison")
    for frame, name in [(checks, "task2_feature_checks.csv"), (summary, "task2_handcheck_summary.csv"), (boundary, "task2_boundary_examples.csv")]:
        frame.to_csv(a.results_dir / name, index=False, date_format="%Y-%m-%d", lineterminator="\n")
    a.daily_output.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(a.daily_output, index=False, date_format="%Y-%m-%d", lineterminator="\n")
    s = summary.iloc[0]
    counts = excluded.groupby("exclusion_reason").size()
    first, last = table.loc[table.split.eq("train"), "origin_date"].agg(["min", "max"])
    vf, vl = table.loc[table.split.eq("validation"), "origin_date"].agg(["min", "max"])
    report = ["# Task 2 Step 2 feature and split review", "",
        "The implementation and independent checks are complete. Hiếu's peer review is pending; the shared cohort/clipping decision remains Step 4.", "",
        f"Panel SHA256: `{sha256(a.panel)}`.", f"Learning-table SHA256: `{sha256(a.table)}`.",
        f"Validation-key SHA256: `{key_hash}` (matches Task 1).",
        f"Checker SHA256: `{sha256(__file__)}`.", "", "## Independent checks", "",
        f"All {len(table):,} learning rows match a separate cumulative-sum reconstruction of the three features and seven-day target (absolute tolerance 1e-8). Keys, country, activity group, target dates and split assignments match exactly.",
        f"Training-only eligibility, activity bands and the 20% candidate flag match for all {len(ports)} ports. All {len(excluded):,} excluded rows match by key and reason. Observed zeros remain in the source and target windows.",
        "", f"Training origins: {first:%Y-%m-%d} through {last:%Y-%m-%d}; validation origins: {vf:%Y-%m-%d} through {vl:%Y-%m-%d}.",
        "Observations after the validation cutoff are removed before checking feature and label windows. No test targets or scores are generated.",
        "", "## Direct calendar hand check", "", f"Port `{a.example_port}`, origin {s.origin_date:%Y-%m-%d}, split `{s.split}`.", "",
        "| Quantity | Calendar days | Direct calculation |", "|---|---|---:|",
        f"| Cargo 7 days | {s.history_7d_start:%Y-%m-%d} to {s.origin_date:%Y-%m-%d} | {s.cargo_7d:,.0f} tonnes |",
        f"| Calls 7 days | Same seven dates | {s.calls_7d:,.0f} calls |",
        f"| Cargo mean 28 days | {s.history_28d_start:%Y-%m-%d} to {s.origin_date:%Y-%m-%d} | {s.cargo_28d_sum:,.0f} / 28 = {s.cargo_mean_28d:,.6f} tonnes/day |",
        f"| Target 7 days | {s.target_start:%Y-%m-%d} to {s.target_end:%Y-%m-%d} | {s.target_7d:,.0f} tonnes |", "",
        "The 35 daily input rows and inclusion flags are exported locally to `data/task2_handcheck_daily.csv` by default. The compact summary and boundary examples are committed; daily source rows remain local.",
        "", "## Exclusions", "", "| Reason | Rows |", "|---|---:|"]
    report += [f"| {reason} | {n:,} |" for reason, n in counts.items()]
    train_end, validation_end = pd.Timestamp(config["train_end"]), pd.Timestamp(config["validation_end"])
    report += ["", "The first 27 origins per port lack a full 28-day history. "
        f"Origins {train_end-pd.Timedelta(days=6):%Y-%m-%d} through {train_end-pd.Timedelta(days=1):%Y-%m-%d} cross the training target boundary. "
        f"Origins {validation_end-pd.Timedelta(days=6):%Y-%m-%d} through {validation_end:%Y-%m-%d} need targets beyond validation and are excluded from this step.",
        "", "## Hiếu review checklist", "", "1. Sum the flagged dates in the local hand-check CSV and compare the four values above.",
        "2. Inspect `task2_boundary_examples.csv`, especially 24/25/31 December 2024 and 24/25 December 2025.",
        "3. Confirm the validation-key hash is unchanged from Task 1 and review the cohort proposal before Step 3/4.", ""]
    (a.results_dir / "task2_feature_review.md").write_text("\n".join(report), encoding="utf-8")
    print(f"PASS: {len(table):,} learning rows, {len(ports)} training port records, {len(excluded):,} exclusions.")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
