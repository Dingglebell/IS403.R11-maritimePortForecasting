"""Build Task 2 train/validation windows without using test-period observations."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["cargo_7d", "calls_7d", "cargo_mean_28d"]
KEYS = ["port_id", "origin_date"]
PANEL_COLUMNS = ["date", "port_id", "country_iso3", "import_tonnes",
                 "export_tonnes", "portcalls", "cargo_tonnes"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_panel(path):
    return pd.read_csv(path, parse_dates=["date"],
                       dtype={"port_id": "string", "country_iso3": "string"})


def validate_config(config):
    if config["horizon_days"] != 7 or config["history_days"] != [7, 28]:
        raise ValueError("This pipeline requires a 7-day target and 7/28-day histories")
    start, a, b, end = [pd.Timestamp(config[k]) for k in
                        ["train_start", "train_end", "validation_end", "test_end"]]
    if not start < a < b < end:
        raise ValueError("Set chronological train_start/train_end/validation_end/test_end")
    if config["port_selection"]["handoff_rule"] != "complete_training_coverage":
        raise ValueError("Review the implementation before changing the cohort rule")
    if not config.get("pool_ports") or config.get("refit_before_test"):
        raise ValueError("This pipeline implements pooled models fitted on training only")
    if config.get("clip_negative_predictions") not in (None, True, False):
        raise ValueError("clip_negative_predictions must be null, true or false")
    return start, a, b


def build_learning_table(panel, config):
    """Return complete common rows, training-only port metadata and exclusions.

    Task 1's proposed complete-training-coverage rule is reused, not approved here.
    Test rows are removed before any feature, target or selection calculation.
    """
    start, a, b = validate_config(config)
    if set(PANEL_COLUMNS) - set(panel):
        raise ValueError("Panel does not match data/data_dictionary.md")
    f = panel.loc[panel.date.between(start, b), PANEL_COLUMNS].copy()
    if f.empty:
        raise ValueError("No observations in the training/validation period")
    for col in ["port_id", "country_iso3"]:
        if f[col].isna().any() or f[col].astype(str).str.strip().eq("").any():
            raise ValueError(f"Unknown identifier: {col}")
    if not f.country_iso3.str.fullmatch(r"[A-Z]{3}").all():
        raise ValueError("Expected uppercase ISO3 country codes")
    f = f.sort_values(["port_id", "date"]).reset_index(drop=True)
    if f.duplicated(["port_id", "date"]).any():
        raise ValueError("Duplicate port/date keys")
    if not f.date.eq(f.date.dt.normalize()).all():
        raise ValueError("Expected daily midnight observation labels")
    if not f.groupby("port_id").date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Calendar gap: run prepare_data.py; never compress missing days")
    if f.groupby("port_id").country_iso3.nunique().gt(1).any():
        raise ValueError("A port maps to multiple countries")
    for col in PANEL_COLUMNS[3:]:
        f[col] = pd.to_numeric(f[col], errors="raise")
        values = f[col].dropna()
        if values.lt(0).any() or not np.isfinite(values).all():
            raise ValueError(f"Invalid nonnegative finite measurement: {col}")
    if f.portcalls.dropna().mod(1).ne(0).any():
        raise ValueError("Port calls must be whole counts")
    expected = f.import_tonnes + f.export_tonnes
    if not np.allclose(f.cargo_tonnes, expected, equal_nan=True, rtol=0, atol=1e-8):
        raise ValueError("cargo_tonnes must equal import_tonnes + export_tonnes")

    train = f.loc[f.date.le(a)].copy()
    train["known_cargo"] = train.cargo_tonnes.notna()
    train["known_calls"] = train.portcalls.notna()
    train["active"] = train.cargo_tonnes.gt(0)
    n_days = len(pd.date_range(start, a))
    ports = train.groupby("port_id").agg(
        country_iso3=("country_iso3", "first"), train_known_days=("known_cargo", "sum"),
        train_calls_known_days=("known_calls", "sum"), train_active_days=("active", "sum"))
    ports["train_calendar_days"] = n_days
    ports["train_active_share"] = ports.train_active_days / n_days
    ports["selected"] = ports.train_known_days.eq(n_days) & ports.train_calls_known_days.eq(n_days)
    cuts = config["port_selection"]["activity_group_cuts"]
    if len(cuts) != 2 or not 0 < cuts[0] < cuts[1] < 1:
        raise ValueError("Expected two increasing activity-group cuts between zero and one")
    ports["activity_group"] = np.select(
        [ports.train_active_share.lt(cuts[0]), ports.train_active_share.lt(cuts[1])],
        ["low", "medium"], default="high")
    ports["candidate_active20"] = ports.selected & ports.train_active_share.ge(
        config["port_selection"]["candidate_active_share"])
    ports["reason"] = np.where(ports.selected, "complete_training_cargo_and_calls",
                               "incomplete_training_cargo_or_calls")
    if not ports.selected.any():
        raise ValueError("No ports have complete training coverage")

    g = f.groupby("port_id")
    f["cargo_7d"] = g.cargo_tonnes.transform(lambda s: s.rolling(7, min_periods=7).sum())
    f["calls_7d"] = g.portcalls.transform(lambda s: s.rolling(7, min_periods=7).sum())
    f["cargo_mean_28d"] = g.cargo_tonnes.transform(lambda s: s.rolling(28, min_periods=28).mean())
    f["target_7d"] = g.cargo_tonnes.transform(lambda s: s.rolling(7, min_periods=7).sum().shift(-7))
    f = f.rename(columns={"date": "origin_date"})
    f["target_start"] = f.origin_date + pd.Timedelta(days=1)
    f["target_end"] = f.origin_date + pd.Timedelta(days=7)
    f["split"] = np.select([f.target_end.le(a), f.origin_date.ge(a) & f.target_end.le(b)],
                            ["train", "validation"], default="excluded")
    selected = f.port_id.map(ports.selected).fillna(False)
    f["exclusion_reason"] = np.select([
        ~selected, f.target_end.gt(b), f.split.eq("excluded"),
        f[FEATURES].isna().any(axis=1), f.target_7d.isna()],
        ["incomplete_training_port_coverage", "target_beyond_validation",
         "target_crosses_train_boundary", "incomplete_history", "incomplete_target"], default="")
    excluded = f.loc[f.exclusion_reason.ne(""), [*KEYS, "split", "exclusion_reason"]].copy()
    keep = f.loc[f.exclusion_reason.eq("")].copy()
    keep["activity_group"] = keep.port_id.map(ports.activity_group)
    columns = [*KEYS, "country_iso3", "activity_group", *FEATURES, "target_start",
               "target_end", "target_7d", "split"]
    for split in ["train", "validation"]:
        if keep.loc[keep.split.eq(split)].empty:
            raise ValueError(f"No complete {split} samples")
    return keep[columns].reset_index(drop=True), ports.reset_index(), excluded


def export_features(panel_path, config_path, output=Path("data/learning_table.csv"),
                    results_dir=Path("results")):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    table, ports, excluded = build_learning_table(read_panel(panel_path), config)
    output, results_dir = Path(output), Path(results_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False, date_format="%Y-%m-%d", lineterminator="\n")
    ports.to_csv(results_dir / "task2_ports.csv", index=False, lineterminator="\n")
    excluded.to_csv(results_dir / "task2_window_exclusions.csv", index=False,
                    date_format="%Y-%m-%d", lineterminator="\n")
    excluded.groupby(["split", "exclusion_reason"]).size().rename("rows").reset_index().to_csv(
        results_dir / "task2_exclusion_summary.csv", index=False, lineterminator="\n")
    summary = table.groupby("split").agg(rows=("port_id", "size"), ports=("port_id", "nunique"),
        first_origin=("origin_date", "min"), last_origin=("origin_date", "max"),
        first_target=("target_start", "min"), last_target=("target_end", "max")).reset_index()
    summary.to_csv(results_dir / "task2_split_summary.csv", index=False, date_format="%Y-%m-%d", lineterminator="\n")
    print(summary.to_string(index=False))
    return table


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--panel", type=Path, default=Path("data/ports_daily.csv"))
    p.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    p.add_argument("--output", type=Path, default=Path("data/learning_table.csv"))
    p.add_argument("--results-dir", type=Path, default=Path("results"))
    a = p.parse_args()
    export_features(a.panel, a.experiment, a.output, a.results_dir)


if __name__ == "__main__":
    main()
