"""Reproduce Task 1 audit and controlled zero-policy validation, never test scores.

This diagnostic is a handoff for Task 2 review, not its production model suite.
Run from the repository root after prepare_data.py; see docs/zero_handling.md.
"""

import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from prepare_data import clean_daily_panel

FEATURES = ["cargo_7d", "calls_7d", "cargo_mean_28d"]
KEYS = ["port_id", "date"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def csv(frame, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", na_rep="", lineterminator="\n")


def md(frame):
    values = frame.copy()
    for col in values:
        if pd.api.types.is_float_dtype(values[col]):
            values[col] = values[col].map(lambda v: "NA" if pd.isna(v) else f"{v:,.4f}")
    return "| " + " | ".join(values.columns) + " |\n| " + " | ".join(["---"] * len(values.columns)) + " |\n" + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in values.itertuples(index=False, name=None))


def training_ports(panel, config):
    dates = pd.date_range(config["train_start"], config["train_end"])
    p = panel.loc[panel.date.between(dates[0], dates[-1])].copy()
    p["active"] = p.cargo_tonnes.gt(0)
    p["known"] = p.cargo_tonnes.notna()
    p["calls_known"] = p.portcalls.notna()
    out = p.groupby("port_id", sort=True).agg(country_iso3=("country_iso3", "first"),
        train_known_days=("known", "sum"), train_active_days=("active", "sum"),
        train_calls_known_days=("calls_known", "sum")).reset_index()
    out["train_calendar_days"] = len(dates)
    out["train_coverage"] = out.train_known_days / len(dates)
    out["train_active_share"] = out.train_active_days / len(dates)
    out["train_active_share_observed"] = out.train_active_days / out.train_known_days.replace(0, np.nan)
    lo, hi = config["port_selection"]["activity_group_cuts"]
    out["activity_group"] = np.select([out.train_active_share.lt(lo), out.train_active_share.lt(hi)], ["low", "medium"], default="high")
    out["selected"] = out.train_known_days.eq(len(dates)) & out.train_calls_known_days.eq(len(dates))
    out["candidate_active20"] = out.selected & out.train_active_share.ge(config["port_selection"]["candidate_active_share"])
    out["reason"] = np.where(out.selected, "complete_training_cargo_and_calls; observed_zeros_retained", "incomplete_training_cargo_or_calls")
    out["active20_reason"] = np.where(out.candidate_active20, "complete_training_coverage_and_active_share_ge_0.20", np.where(out.selected, "training_active_share_lt_0.20", "incomplete_training_cargo_or_calls"))
    out["rule_status"] = "Task1_handoff_recommendation_pending_joint_review"
    return out


def zero_runs(panel):
    rows = []
    for pid, g in panel.groupby("port_id", sort=True):
        g = g.sort_values("date").reset_index(drop=True)
        zero = g.cargo_tonnes.eq(0)
        # Unknown measurements and calendar discontinuities both break runs.
        segments = (zero.ne(zero.shift()) | g.date.diff().ne(pd.Timedelta(days=1))).cumsum()
        for _, run in g.loc[zero].groupby(segments[zero]):
            rows.append({"port_id": pid, "country_iso3": run.country_iso3.iloc[0], "start": run.date.iloc[0],
                "end": run.date.iloc[-1], "days": len(run), "days_with_calls": int(run.portcalls.gt(0).sum()),
                "calls": run.portcalls.sum(min_count=1), "left_censored": run.index[0] == 0,
                "right_censored": run.index[-1] == len(g)-1})
    return pd.DataFrame(rows, columns=["port_id", "country_iso3", "start", "end", "days", "days_with_calls", "calls", "left_censored", "right_censored"])


def build_windows(panel, config, replace_zeros=False):
    """Discard test measurements before computing any window or replacement."""
    start, a, b = map(pd.Timestamp, [config["train_start"], config["train_end"], config["validation_end"]])
    f = panel.loc[panel.date.between(start, b)].sort_values(KEYS).copy()
    if f.duplicated(KEYS).any() or not f.groupby("port_id").date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Unique, complete daily calendar required")
    cargo = f.groupby("port_id").cargo_tonnes
    f["history_cargo"] = f.cargo_tonnes.astype(float)
    if replace_zeros:
        past_positive = cargo.transform(lambda s: s.where(s.gt(0)).shift(1).rolling(28, min_periods=1).mean())
        f.loc[f.cargo_tonnes.eq(0), "history_cargo"] = past_positive.fillna(0)
    history = f.groupby("port_id").history_cargo
    f["cargo_7d"] = history.transform(lambda s: s.rolling(7, min_periods=7).sum())
    f["cargo_mean_28d"] = history.transform(lambda s: s.rolling(28, min_periods=28).mean())
    f["calls_7d"] = f.groupby("port_id").portcalls.transform(lambda s: s.rolling(7, min_periods=7).sum())
    # Always score the original observed calendar-day total, never an imputed label.
    f["y_true"] = cargo.transform(lambda s: s.rolling(7, min_periods=7).sum().shift(-7))
    f["target_start"] = f.date + pd.Timedelta(days=1)
    f["target_end"] = f.date + pd.Timedelta(days=7)
    f["split"] = np.select([f.target_end.le(a), f.date.ge(a) & f.target_end.le(b)], ["train", "validation"], default="excluded")
    f["complete"] = f[[*FEATURES, "y_true"]].notna().all(axis=1)
    f["exclusion_reason"] = np.select([f.date.eq(b), f.target_end.gt(b), f.split.eq("excluded"),
        f[FEATURES].isna().any(axis=1), f.y_true.isna()],
        ["origin_reserved_for_test", "target_beyond_validation", "target_crosses_train_boundary", "incomplete_history", "incomplete_target"], default="")
    return f


def positive_observation_spans(training):
    """Calendar horizon after deleting zero days: seven next positive observations."""
    spans = []
    for pid, g in training.loc[training.cargo_tonnes.gt(0)].groupby("port_id", sort=True):
        dates = g.date.sort_values().to_numpy(dtype="datetime64[D]")
        if len(dates) > 7:
            spans.append(pd.DataFrame({"port_id": pid, "days": (dates[7:]-dates[:-7]).astype(int)}))
    return pd.concat(spans, ignore_index=True) if spans else pd.DataFrame(columns=["port_id", "days"])


def fit_ols(train, evaluation):
    x = train[FEATURES].to_numpy(float)
    if not len(x):
        raise ValueError("Empty training set")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1
    design = np.column_stack([np.ones(len(x)), (x-mean)/scale])
    coef, _, rank, _ = np.linalg.lstsq(design, train.y_true.to_numpy(float), rcond=None)
    pred = np.column_stack([np.ones(len(evaluation)), (evaluation[FEATURES].to_numpy(float)-mean)/scale]) @ coef
    if not np.isfinite(pred).all():
        raise ValueError("Nonfinite prediction")
    return pred, {"n_training_rows": len(train), "rank": int(rank), "mean": mean.tolist(), "scale": scale.tolist(), "coefficients": coef.tolist()}


def metrics(f):
    if f.empty:
        return {"n": 0, "ports": 0, "MAE": np.nan, "RMSE": np.nan, "WAPE_pct": np.nan, "macro_port_MAE": np.nan, "bias": np.nan, "zero_actual_windows": 0}
    error = f.y_pred - f.y_true
    denom = f.y_true.sum()
    return {"n": len(f), "ports": f.port_id.nunique(), "MAE": error.abs().mean(), "RMSE": np.sqrt((error**2).mean()),
        "WAPE_pct": 100*error.abs().sum()/denom if denom else np.nan,
        "macro_port_MAE": error.abs().groupby(f.port_id).mean().mean(), "bias": error.mean(),
        "zero_actual_windows": int(f.y_true.eq(0).sum())}


def block_interval(daily_differences, block_days=28, repeats=2000, seed=42):
    """Paired moving-block bootstrap over dates, all ports move together."""
    d = np.asarray(daily_differences, float)
    if len(d) < block_days:
        raise ValueError("Too few dates for the prespecified block")
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(d)-block_days+1, size=(repeats, int(np.ceil(len(d)/block_days))))
    indices = (starts[..., None] + np.arange(block_days)).reshape(repeats, -1)[:, :len(d)]
    lo, hi = np.quantile(d[indices].mean(axis=1), [.025, .975])
    return float(d.mean()), float(lo), float(hi)


def audit(raw_dir, panel_path, config, out, data_dir=Path("data")):
    snapshot = json.loads((raw_dir / "snapshot.json").read_text(encoding="utf-8"))
    entries = {Path(e["file"]).name: e for e in snapshot["files"]}
    frames, manifest = [], []
    for path in sorted(raw_dir.glob("*.csv")):
        item = entries[path.name]
        digest = sha256(path)
        if digest != item["sha256"]:
            raise ValueError(f"Changed source: {path.name}")
        raw = pd.read_csv(path, dtype={"portid": "string", "ISO3": "string"})
        frames.append(raw)
        # Explicit allowlist: never export signed redirects or access tokens.
        manifest.append({"file": path.name, "source_url": item["source_url"], "download_url": item["download_url"],
            "verified_at_utc": item["verified_at_utc"], "downloaded_at_utc": item.get("downloaded_at_utc"),
            "sha256": digest, "bytes": path.stat().st_size, "rows": len(raw), "ports": raw.portid.nunique(),
            "start": str(raw.date.min())[:10], "end": str(raw.date.max())[:10], "license_url": item["license_url"]})
    bundle = hashlib.sha256("".join(f"{e['file']}\t{e['sha256']}\n" for e in manifest).encode()).hexdigest()
    if bundle != config["data_snapshot_sha256"]:
        raise ValueError("Snapshot bundle does not match experiment.json")
    raw = pd.concat(frames, ignore_index=True)
    panel = clean_daily_panel(raw)
    saved = pd.read_csv(panel_path, parse_dates=["date"], dtype={"port_id": "string", "country_iso3": "string"})
    pd.testing.assert_frame_equal(panel.reset_index(drop=True), saved, check_dtype=False)
    dates = pd.to_datetime(raw.date, utc=True)
    for part in ["year", "month", "day"]:
        if not pd.to_numeric(raw[part], errors="raise").eq(getattr(dates.dt, part)).all():
            raise ValueError(f"Inconsistent source {part}")
    metadata = raw[["portid", "portname", "country", "ISO3"]].drop_duplicates()
    if metadata.portid.duplicated().any():
        raise ValueError("Ambiguous port metadata")
    metadata = metadata.rename(columns={"portid": "port_id", "portname": "port_name", "ISO3": "country_iso3"})
    metadata["source_named_offshore_oil_terminal"] = metadata.port_name.str.contains("Offshore Oil Terminal", case=False)
    csv(pd.DataFrame(manifest), data_dir / "source_manifest.csv")
    csv(metadata.sort_values("port_id"), data_dir / "ports_metadata.csv")
    fields = []
    identifiers = {"date", "portid", "portname", "country", "ISO3"}
    for col in raw:
        numeric = pd.to_numeric(raw[col], errors="coerce") if col not in identifiers else None
        fields.append({"field": col, "missing": int(raw[col].isna().sum()),
            "invalid_numeric": int((raw[col].notna() & numeric.isna()).sum()) if numeric is not None else 0,
            "negative": int(numeric.lt(0).sum()) if numeric is not None else 0,
            "nonfinite": int((numeric.notna() & ~np.isfinite(numeric)).sum()) if numeric is not None else 0})
    field_audit = pd.DataFrame(fields)
    csv(field_audit, out / "source_field_audit.csv")
    reconcile = []
    cats = ["container", "dry_bulk", "general_cargo", "roro", "tanker"]
    for prefix in ["portcalls", "import", "export"]:
        diff = raw[prefix] - raw[[f"{prefix}_{c}" for c in cats]].sum(axis=1, min_count=5)
        subtotal = raw[f"{prefix}_cargo"] - raw[[f"{prefix}_{c}" for c in cats[:-1]]].sum(axis=1, min_count=4)
        reconcile.append({"measure": prefix, "total_vs_5_categories_differing_rows": int(diff.ne(0).sum()),
            "max_abs_difference": diff.abs().max(), "cargo_subtotal_vs_4_categories_differing_rows": int(subtotal.ne(0).sum()),
            "max_abs_subtotal_difference": subtotal.abs().max()})
    csv(pd.DataFrame(reconcile), out / "category_reconciliation.csv")
    runs = zero_runs(panel)
    csv(runs, out / "zero_runs.csv")
    long = runs.loc[runs.days.ge(28)]
    p = panel.assign(known=panel.cargo_tonnes.notna(), zero=panel.cargo_tonnes.eq(0),
        positive=panel.cargo_tonnes.gt(0), zero_with_calls=panel.cargo_tonnes.eq(0) & panel.portcalls.gt(0))
    stats = p.groupby("port_id").agg(country_iso3=("country_iso3", "first"), days=("date", "size"), known=("known", "sum"),
        positive_days=("positive", "sum"), zero_days=("zero", "sum"), zero_days_with_calls=("zero_with_calls", "sum")).reset_index()
    stats["zero_pct"] = 100*stats.zero_days/stats.known.replace(0, np.nan)
    stats["longest_zero_run"] = stats.port_id.map(runs.groupby("port_id").days.max()).fillna(0).astype(int)
    stats = stats.merge(metadata.drop(columns="country_iso3"), on="port_id", validate="one_to_one")
    csv(stats, out / "port_audit.csv")
    country = p.groupby("country_iso3").agg(ports=("port_id", "nunique"), rows=("date", "size"), known=("known", "sum"), zero_days=("zero", "sum"), zero_days_with_calls=("zero_with_calls", "sum")).reset_index()
    country["zero_pct"] = country.zero_days/country.known*100
    csv(country, out / "country_audit.csv")
    selection = training_ports(panel, config).merge(metadata[["port_id", "port_name"]], on="port_id", validate="one_to_one")
    spans = positive_observation_spans(panel.loc[panel.date.between(config["train_start"], config["train_end"])])
    distortion = spans.assign(over7=spans.days.gt(7)).groupby("port_id").agg(windows=("days", "size"),
        median_calendar_days=("days", "median"), max_calendar_days=("days", "max"), fraction_over7=("over7", "mean")).reset_index()
    csv(distortion, out / "zero_calendar_distortion.csv")
    csv(selection, out / "port_selection_audit.csv")
    csv(selection.loc[selection.selected], data_dir / "selected_ports.csv")
    retention = selection.groupby("country_iso3").agg(source_ports=("port_id", "size"), retained=("selected", "sum"), active20=("candidate_active20", "sum")).reset_index()
    csv(retention, out / "country_retention.csv")
    fullzero = stats.loc[stats.zero_days.eq(stats.days), ["port_id", "port_name", "country_iso3", "source_named_offshore_oil_terminal"]]
    text = f"""# Data audit (generated)

Source: IMF PortWatch via HDX, locally obtained/verified 18 October 2026. This is not verified as byte-identical to the group's earlier 12 October copy. Individual provenance is in `data/source_manifest.csv`; blank download timestamps were not recorded, not invented.

- Snapshot SHA256: `{bundle}` (sorted filename + TAB + SHA256 + LF, UTF-8).
- Clean CSV SHA256: `{sha256(panel_path)}`.
- Rows: {len(panel):,}; source rows: {len(raw):,}; port/terminal IDs: {panel.port_id.nunique()}; countries: {panel.country_iso3.nunique()}.
- Dates: {panel.date.min():%Y-%m-%d} to {panel.date.max():%Y-%m-%d}; unique port/date keys verified.
- Added missing calendar rows: {len(panel)-len(raw)}; unknown cargo: {panel.cargo_tonnes.isna().sum()}; required negative/invalid/nonfinite values: none (cleaner rejects them).
- Observed zero cargo: {p.zero.sum():,}/{p.known.sum():,} ({100*p.zero.sum()/p.known.sum():.4f}%); positive cargo: {p.positive.sum():,}.
- Zero cargo with positive calls: {p.zero_with_calls.sum():,} ({100*p.zero_with_calls.sum()/p.zero.sum():.4f}% of observed zeros).
- Zero runs >=28 days: {len(long):,}, across {long.port_id.nunique()} IDs; {long.days_with_calls.gt(0).sum()} such runs contain positive calls. These are review flags, not evidence of missingness. Boundary runs are censored.
- Source names containing Offshore Oil Terminal: {metadata.source_named_offshore_oil_terminal.sum()}; no name-based exclusions.
- No zero removal, imputation, clipping, outlier deletion or deduplication. Required invalid input stops cleaning. All saved panel values matched a fresh reconstruction from raw CSVs.
- Training-only illustration: if zero days were deleted, the next seven positive observations would span more than seven calendar days in {100*spans.days.gt(7).mean():.4f}% of {len(spans):,} eligible positive-origin windows; median {spans.days.median():g} days, maximum {spans.days.max():g}. This is an invalid change of target, not an alternative scored forecast. Per-port detail: `zero_calendar_distortion.csv`.

## Country coverage (full snapshot; descriptive only)

{md(country)}

## Source-field checks

{md(field_audit)}

## Category reconciliation

{md(pd.DataFrame(reconcile))}

Keep published totals. Do not sum subtotals and categories together. The cause of small cargo discrepancies is unverified; they are not silently corrected.

## Entire-snapshot zero-cargo entities

{md(fullzero)}

These are descriptive retrospective flags, never training eligibility criteria. Neither zero estimates nor positive calls establish true cargo throughput.

## Training-only country retention

{md(retention)}

The handoff keeps complete-training-coverage ports; the 20% active-day filter is a sensitivity candidate. Both count training calendar days, including genuine zeros. Joint Task 2 review is pending. See `docs/zero_handling.md` for validation evidence and `data/data_dictionary.md` for field meanings.
"""
    (out / "data_audit.md").write_text(text, encoding="utf-8")
    return panel, selection, stats


def evaluate(panel, selection, config, out, panel_path=Path("data/ports_daily.csv"), config_path=Path("experiment.json")):
    original = build_windows(panel, config)
    altered = build_windows(panel, config, replace_zeros=True)
    pd.testing.assert_series_equal(original.y_true, altered.y_true)
    if not original.complete.equals(altered.complete):
        raise ValueError("Policies must preserve complete-window masks")
    ids = set(selection.loc[selection.selected, "port_id"])
    active = set(selection.loc[selection.candidate_active20, "port_id"])
    if not active or not ids:
        raise ValueError("Empty eligible cohort")
    valid = original.split.eq("validation") & original.complete & original.port_id.isin(ids)
    training = original.split.eq("train") & original.complete & original.port_id.isin(ids)
    ev = original.loc[valid].copy()
    ev["activity_group"] = ev.port_id.map(selection.set_index("port_id").activity_group)
    if ev.groupby("date").size().nunique() != 1 or ev.groupby("port_id").size().nunique() != 1:
        raise ValueError("This date-block bootstrap requires a balanced validation panel")
    csv(ev[[*KEYS, "target_start", "target_end"]].rename(columns={"date": "origin_date"}), out / "validation_keys.csv")
    excluded = original.loc[original.exclusion_reason.ne("") | ~original.port_id.isin(ids), [*KEYS, "split", "exclusion_reason"]].copy()
    excluded.loc[excluded.exclusion_reason.eq(""), "exclusion_reason"] = "incomplete_training_port_coverage"
    csv(excluded, out / "window_exclusions.csv")
    csv(excluded.groupby(["split", "exclusion_reason"]).size().rename("rows").reset_index(), out / "window_exclusion_summary.csv")
    predictions, fits, training_counts = [], {}, []
    policies = config["task1_diagnostic"]["policies"]
    for policy in policies:
        table = altered if policy == "replace_zero_history" else original
        mask = training.copy()
        if policy == "drop_zero_targets":
            mask &= original.y_true.gt(0)
        if policy == "active20":
            mask &= original.port_id.isin(active)
        pred, fits[policy] = fit_ols(table.loc[mask], table.loc[valid])
        training_counts.append({"policy": policy, "training_rows": int(mask.sum()), "excluded_training_rows": int(training.sum()-mask.sum()),
            "training_ports": table.loc[mask, "port_id"].nunique(), "zero_training_targets": int(table.loc[mask, "y_true"].eq(0).sum())})
        removed = original.loc[training & ~mask, [*KEYS]].copy()
        if len(removed):
            removed["policy"] = policy
            csv(removed, out / f"training_exclusions_{policy}.csv")
        for clip in ["nonnegative", "none"]:
            f = ev.copy()
            f["policy"], f["model"], f["clipping"] = policy, "OLS", clip
            f["y_pred"] = np.maximum(pred, 0) if clip == "nonnegative" else pred
            predictions.append(f)
    for policy, values in [("retain_zero", ev.cargo_7d), ("replace_zero_history", altered.loc[valid, "cargo_7d"]), ("always_zero", np.zeros(len(ev)))]:
        f = ev.copy()
        f["policy"], f["model"], f["clipping"] = policy, "seasonal_naive" if policy != "always_zero" else "zero_reference", "not_applicable"
        f["y_pred"] = np.asarray(values)
        predictions.append(f)
    allp = pd.concat(predictions, ignore_index=True)
    # Each policy predicts the same keys/targets; active20 scores only its shared subset below.
    for _, f in allp.groupby(["policy", "model", "clipping"]):
        if f.duplicated(KEYS).any() or not np.array_equal(f.y_true, ev.y_true):
            raise ValueError("Prediction alignment failure")
    exported = allp[["policy", "model", "clipping", "port_id", "country_iso3", "date", "target_start", "target_end", "y_true", "y_pred"]].rename(columns={"date": "origin_date"})
    exported["split"] = "validation"
    exported["feature_set"] = np.where(exported.model.eq("OLS"), "all_three", "cargo_only")
    # Do not export extrapolated predictions to ports excluded by the active20 policy.
    exported = exported.loc[~exported.policy.eq("active20") | exported.port_id.isin(active)]
    csv(exported, out / "zero_policy_predictions.csv")
    scores = []
    for (policy, model, clip), f in allp.groupby(["policy", "model", "clipping"], sort=True):
        for cohort, group in [("all_eligible", f), ("common_active20", f.loc[f.port_id.isin(active)])]:
            if policy == "active20" and cohort == "all_eligible":
                continue
            def add(kind, name, rows):
                scores.append({"policy": policy, "model": model, "clipping": clip, "cohort": cohort, "group_type": kind, "group": str(name), **metrics(rows)})
            add("overall", "all", group)
            add("target", "zero", group.loc[group.y_true.eq(0)])
            add("target", "positive", group.loc[group.y_true.gt(0)])
            for kind, col in [("country", "country_iso3"), ("activity", "activity_group"), ("port", "port_id")]:
                for name, rows in group.groupby(col, sort=True):
                    add(kind, name, rows)
            offset = (group.date-pd.Timestamp(config["train_end"])).dt.days % 7
            for phase in range(7):
                add("weekly_phase", phase, group.loc[offset.eq(phase)])
    scores = pd.DataFrame(scores)
    csv(scores, out / "zero_policy_metrics.csv")
    csv(pd.DataFrame(training_counts), out / "policy_training_counts.csv")
    bootstrap = []
    for policy in ["drop_zero_targets", "replace_zero_history", "active20"]:
        for clip in ["nonnegative", "none"]:
            ref = allp.loc[allp.policy.eq("retain_zero") & allp.model.eq("OLS") & allp.clipping.eq(clip)].set_index(KEYS)
            alt = allp.loc[allp.policy.eq(policy) & allp.model.eq("OLS") & allp.clipping.eq(clip)].set_index(KEYS)
            if policy == "active20":
                ref = ref.loc[ref.index.get_level_values("port_id").isin(active)]
                alt = alt.loc[alt.index.get_level_values("port_id").isin(active)]
            pd.testing.assert_index_equal(ref.index, alt.index)
            diffs = ((alt.y_pred-alt.y_true).abs()-(ref.y_pred-ref.y_true).abs()).groupby(level="date").mean()
            for block_days in [7, config["task1_diagnostic"]["bootstrap_block_days"], 56]:
                point, lo, hi = block_interval(diffs, block_days, config["task1_diagnostic"]["bootstrap_replicates"], config["random_seed"])
                bootstrap.append({"policy_minus_retain": policy, "clipping": clip, "cohort": "common_active20" if policy == "active20" else "all_eligible",
                    "MAE_difference": point, "ci_low": lo, "ci_high": hi, "block_days": block_days, "replicates": config["task1_diagnostic"]["bootstrap_replicates"]})
    csv(pd.DataFrame(bootstrap), out / "paired_block_sensitivity.csv")
    record = {"status": "diagnostic_complete_joint_review_pending", "test_scored": False,
        "last_measurement_used_for_validation": config["validation_end"], "validation_origins": len(ev), "validation_ports": len(ids),
        "origin_first": str(ev.date.min().date()), "origin_last": str(ev.date.max().date()),
        "common_active20_ports": len(active), "common_active20_origins": int(ev.port_id.isin(active).sum()),
        "validation_keys_sha256": sha256(out / "validation_keys.csv"), "panel_sha256": sha256(panel_path),
        "script_sha256": sha256(__file__), "config_sha256": sha256(config_path),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "matplotlib": matplotlib.__version__},
        "fits": fits}
    (out / "task1_run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    primary = scores.loc[scores.group_type.eq("overall") & scores.clipping.ne("none")]
    (out / "zero_validation.md").write_text("# Zero-policy validation (generated)\n\nNo test scores. Joint review pending. Methods and interpretation: `docs/zero_handling.md`.\n\n## Primary scores\n\n" + md(primary) + "\n\n## Training samples\n\n" + md(pd.DataFrame(training_counts)) + "\n\n## Paired date-block sensitivity\n\nNegative difference favours the alternative; intervals are conditional descriptive bootstrap estimates, not proof of causality or generalisation.\n\n" + md(pd.DataFrame(bootstrap)) + "\n", encoding="utf-8")
    return scores, allp


def figures(panel, ports, stats, scores, out, config):
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    # Train/validation only: no future descriptive pattern informs recommendations.
    f = panel.loc[panel.date.between(config["train_start"], config["validation_end"])].copy()
    monthly = f.assign(month=f.date.dt.to_period("M").dt.to_timestamp()).groupby(["country_iso3", "month"]).cargo_tonnes.sum()
    fig, axes = plt.subplots(5, 2, figsize=(12, 12), constrained_layout=True)
    for ax, (country, g) in zip(axes.flat, monthly.groupby(level=0)):
        ax.plot(g.index.get_level_values(1), g/1e6, color="#176B87", lw=1.4)
        ax.axvline(pd.Timestamp(config["train_end"])+pd.Timedelta(days=1), ls="--", color="#A34A28")
        ax.set_title(country); ax.set_ylabel("Million estimated tonnes/month")
    fig.suptitle("Estimated import + export, 2019–2025; dashed line starts validation")
    fig.savefig(out / "cargo_history.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4.6), constrained_layout=True)
    ax.hist(ports.train_active_share, bins=np.linspace(0, 1, 21), color="#176B87", edgecolor="white")
    ax.axvline(.2, color="#A34A28", ls="--", label="20% candidate")
    ax.set(xlabel="Positive-cargo days / training calendar days", ylabel="Port/terminal IDs", title="Training activity distribution (2019–2024)")
    ax.legend(); fig.savefig(out / "activity_rates.png", dpi=160); plt.close(fig)
    means = f.groupby("port_id").agg(cargo=("cargo_tonnes", "mean"), calls=("portcalls", "mean"))
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.scatter(means.calls, means.cargo, alpha=.65, color="#176B87", s=24)
    ax.set(xscale="symlog", yscale="symlog", xlabel="Mean daily port calls (symlog)", ylabel="Mean daily estimated cargo, tonnes (symlog)", title="Cargo and calls across ports, 2019–2025")
    fig.savefig(out / "cargo_vs_calls.png", dpi=160); plt.close(fig)
    chart = scores.loc[scores.cohort.eq("all_eligible") & scores.model.eq("OLS") & scores.clipping.eq("nonnegative") & scores.group_type.isin(["overall", "target"])].copy()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4), constrained_layout=True)
    labels = {"retain_zero": "Keep zeros", "drop_zero_targets": "Drop zero targets\n(train only)", "replace_zero_history": "Replace zero\nhistory"}
    for ax, group in zip(axes, ["all", "zero", "positive"]):
        g = chart.loc[chart.group.eq(group)].set_index("policy").loc[list(labels)]
        ax.bar(list(labels.values()), g.MAE, color=["#176B87", "#A34A28", "#D6A13D"])
        ax.set_title(f"{group.title()} target windows (n={int(g.n.iloc[0]):,})")
        ax.set_ylabel("MAE, tonnes / 7-day target"); ax.tick_params(axis="x", labelsize=9)
    fig.suptitle("Validation 2025: same rows, pooled OLS with nonnegative predictions")
    fig.savefig(out / "zero_policy_comparison.png", dpi=160); plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/hdx_2026-10-18"))
    parser.add_argument("--panel", type=Path, default=Path("data/ports_daily.csv"))
    parser.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    out = args.results_dir; out.mkdir(parents=True, exist_ok=True)
    config = json.loads(args.experiment.read_text(encoding="utf-8"))
    if config["horizon_days"] != 7 or config["history_days"] != [7, 28]:
        parser.error("This diagnostic implements the protocol's 7-day target and 7/28-day histories")
    if not config["train_start"] < config["train_end"] < config["validation_end"] < config["test_end"]:
        parser.error("Chronological observation periods required")
    panel, ports, stats = audit(args.raw_dir, args.panel, config, out, args.data_dir)
    scores, _ = evaluate(panel, ports, config, out, args.panel, args.experiment)
    figures(panel, ports, stats, scores, out / "figures", config)
    print("Task 1 audit and validation complete. Test not scored. Joint review pending.")
    print(scores.loc[scores.group_type.eq("overall") & scores.clipping.ne("none"), ["policy", "model", "cohort", "n", "MAE", "RMSE", "WAPE_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
