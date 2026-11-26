"""Score aligned cargo forecasts against a common reference learning table."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from features import KEYS, sha256


VARIANT = ["model", "feature_set"]
METADATA = ["country_iso3", "target_start", "target_end", "y_true"]
FORECAST_COLUMNS = [*VARIANT, "split", *KEYS, *METADATA, "y_pred"]
ACTIVITY_GROUPS = ["low", "medium", "high"]


def require_columns(frame, columns, name):
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {', '.join(sorted(missing))}")


def reference_rows(table, config, split):
    columns = [*KEYS, "country_iso3", "activity_group", "target_start", "target_end", "target_7d"]
    require_columns(table, ["split", *columns], "Reference")
    ref = table.loc[table.split.eq(split), columns].rename(columns={"target_7d": "y_true"}).copy()
    if ref.empty or ref.isna().any().any() or ref.duplicated(KEYS).any():
        raise ValueError(f"Reference {split} rows must be complete, nonempty and uniquely keyed")
    if not ref.activity_group.isin(ACTIVITY_GROUPS).all():
        raise ValueError("Reference must use the training-defined low, medium and high activity groups")
    if ref.groupby("port_id")[["country_iso3", "activity_group"]].nunique().gt(1).any().any():
        raise ValueError("Reference country and activity group must be constant for each port")
    if not np.isfinite(ref.y_true).all() or ref.y_true.lt(0).any():
        raise ValueError("Reference actuals must be finite and nonnegative")

    origin = pd.to_datetime(ref.origin_date, format="%Y-%m-%d", errors="raise")
    target_start = origin + pd.Timedelta(days=1)
    target_end = origin + pd.Timedelta(days=7)
    if not (ref.origin_date.eq(origin.dt.strftime("%Y-%m-%d")) &
            ref.target_start.eq(target_start.dt.strftime("%Y-%m-%d")) &
            ref.target_end.eq(target_end.dt.strftime("%Y-%m-%d"))).all():
        raise ValueError("Reference windows must cover days t+1 through t+7")
    cutoff, end = ("train_end", "validation_end") if split == "validation" else ("validation_end", "test_end")
    first_origin = pd.Timestamp(config[cutoff])
    if not (origin.ge(first_origin) & target_end.le(pd.Timestamp(config[end]))).all():
        raise ValueError(f"Reference contains origins or targets outside the {split} window")
    ref["weekly_phase"] = (origin - first_origin).dt.days.mod(7)
    return ref


def align_forecasts(predictions, reference, split, activity_group=None):
    require_columns(predictions, FORECAST_COLUMNS, "Forecasts")
    if predictions.empty or predictions[[*VARIANT, "split", *KEYS]].isna().any().any():
        raise ValueError("Forecasts must contain rows with model, feature set, split and keys")
    if not predictions.split.eq(split).all():
        raise ValueError(f"All forecast rows must have split={split}")
    if "clipping" in predictions and not predictions.clipping.fillna("nonnegative").eq("nonnegative").all():
        raise ValueError("Use one nonnegative forecast variant per model and feature set")

    expected = reference
    outside_scope = []
    if activity_group is not None:
        expected = reference.loc[reference.activity_group.eq(activity_group)]
        outside_scope = reference.loc[~reference.activity_group.eq(activity_group), "port_id"].unique()
    if expected.empty:
        raise ValueError("No reference rows for this cohort")

    coverage, aligned = [], []
    for (model, features), variant in predictions.groupby(VARIANT, sort=True):
        variant = variant.loc[~variant.port_id.isin(outside_scope), [*KEYS, *METADATA, "y_pred"]]
        unique = variant.drop_duplicates(KEYS)
        joined = expected.merge(unique, on=KEYS, how="outer", indicator=True,
                                suffixes=("", "_forecast"), validate="one_to_one")
        matched = joined.loc[joined._merge.eq("both")].copy()
        same_metadata = np.logical_and.reduce([
            matched[name].eq(matched[f"{name}_forecast"]).fillna(False) for name in METADATA
        ])
        valid_forecast = np.isfinite(matched.y_pred) & matched.y_pred.ge(0)
        row = {"model": model, "feature_set": features, "expected_rows": len(expected),
               "forecast_rows": len(variant), "matched_rows": len(matched),
               "missing_rows": int(joined._merge.eq("left_only").sum()),
               "extra_rows": int(joined._merge.eq("right_only").sum()),
               "duplicate_rows": len(variant) - len(unique),
               "mismatched_actual_or_metadata_rows": int((~same_metadata).sum()),
               "invalid_prediction_rows": int((~valid_forecast.fillna(False)).sum())}
        coverage.append(row)
        if any(row[field] for field in ("missing_rows", "extra_rows", "duplicate_rows",
                                        "mismatched_actual_or_metadata_rows", "invalid_prediction_rows")):
            continue
        matched["model"], matched["feature_set"], matched["split"] = model, features, split
        aligned.append(matched[[*FORECAST_COLUMNS, "activity_group", "weekly_phase"]])

    report = pd.DataFrame(coverage)
    if len(aligned) != len(report):
        raise ValueError("Forecast comparison failed. Correct the reported rows before scoring.\n"
                         + report.to_string(index=False))
    return pd.concat(aligned, ignore_index=True), report


def score(aligned, scope):
    rows, largest_errors = [], []
    for (model, features, split), data in aligned.groupby([*VARIANT, "split"], sort=True):
        data = data.copy()
        data["error"] = data.y_pred - data.y_true
        data["abs_error"] = data.error.abs()
        data["squared_error"] = data.error ** 2
        data["actual_volume"] = np.where(data.y_true.eq(0), "zero", "positive")
        groups = [("overall", [("all", data)])]
        for name, column in [("country", "country_iso3"), ("activity", "activity_group"),
                             ("port", "port_id"), ("actual_volume", "actual_volume"),
                             ("weekly_phase", "weekly_phase")]:
            groups.append((name, data.groupby(column, sort=True)))
        for group_type, subsets in groups:
            for group, sub in subsets:
                total = sub.y_true.sum()
                rows.append({"model": model, "feature_set": features, "split": split, "scope": scope,
                             "group_type": group_type, "group": group, "n_rows": len(sub),
                             "n_ports": sub.port_id.nunique(), "zero_actual_rows": int(sub.y_true.eq(0).sum()),
                             "MAE": sub.abs_error.mean(), "RMSE": np.sqrt(sub.squared_error.mean()),
                             "WAPE_pct": 100 * sub.abs_error.sum() / total if total > 0 else np.nan,
                             "macro_port_MAE": sub.groupby("port_id").abs_error.mean().mean(),
                             "mean_bias": sub.error.mean()})
        largest_errors.append(data.nlargest(10, "abs_error")[[*FORECAST_COLUMNS, "activity_group", "error", "abs_error"]])
    return pd.DataFrame(rows), pd.concat(largest_errors, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forecasts", type=Path, nargs="+", required=True)
    parser.add_argument("--reference", type=Path, default=Path("data/learning_table.csv"))
    parser.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--activity-group", choices=ACTIVITY_GROUPS)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    scope = args.activity_group or "all_eligible"
    out = args.out_dir or Path("results") / f"task5_{args.split}" / scope
    try:
        config = json.loads(args.experiment.read_text(encoding="utf-8"))
        reference = reference_rows(pd.read_csv(args.reference, dtype={"port_id": "string"}), config, args.split)
        predictions = pd.concat([pd.read_csv(path, dtype={"port_id": "string"}) for path in args.forecasts],
                                ignore_index=True)
        aligned, coverage = align_forecasts(predictions, reference, args.split, args.activity_group)
        metrics, errors = score(aligned, scope)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))

    try:
        record = {"split": args.split, "scope": scope, "variants": len(coverage),
                  "rows_per_variant": int(coverage.expected_rows.iloc[0]),
                  "reference_sha256": sha256(args.reference), "experiment_sha256": sha256(args.experiment),
                  "evaluator_sha256": sha256(Path(__file__)),
                  "forecasts": [{"file": path.name, "sha256": sha256(path)} for path in args.forecasts]}
        out.mkdir(parents=True, exist_ok=True)
        for frame, filename in [(metrics, "metrics.csv"), (coverage, "coverage.csv"),
                                (errors, "highest_error_predictions.csv")]:
            frame.to_csv(out / filename, index=False, lineterminator="\n")
        (out / "evaluation_run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    except OSError as exc:
        parser.error(f"Could not save the evaluation. Check the input files and choose a writable --out-dir. {exc}")
    print(metrics.loc[metrics.group_type.eq("overall"), [*VARIANT, "n_rows", "MAE", "RMSE", "WAPE_pct"]].to_string(index=False))
    print(f"Wrote {args.split} results for {scope} to {out}")


if __name__ == "__main__":
    main()
