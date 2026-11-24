"""Recreate the fixed Task 5 holdout forecasts and score them on aligned keys."""

import argparse
import importlib.util
import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from baselines import check_learning_table, fit_regression
from evaluate import FORECAST_COLUMNS, align_forecasts, reference_rows, score
from features import FEATURES, KEYS, read_panel, sha256, validate_config


def build_test_windows(panel, ports, config):
    """Use training-derived port groups and calendar windows through each origin."""
    _, _, first_origin = validate_config(config)
    last_target = pd.Timestamp(config["test_end"])
    calendar = pd.date_range(first_origin - pd.Timedelta(days=27), last_target)
    cohort = ports.loc[ports.selected, ["port_id", "country_iso3", "activity_group"]]
    if cohort.empty or cohort.port_id.duplicated().any() or cohort.isna().any().any():
        raise ValueError("Invalid frozen port cohort")

    daily = panel.loc[panel.port_id.isin(cohort.port_id) & panel.date.isin(calendar),
                      ["port_id", "date", "cargo_tonnes", "portcalls"]]
    if daily.duplicated(["port_id", "date"]).any():
        raise ValueError("Duplicate port/date in the holdout panel")
    grid = pd.MultiIndex.from_product([cohort.port_id.sort_values(), calendar], names=["port_id", "date"])
    daily = daily.set_index(["port_id", "date"]).reindex(grid).reset_index()
    for col in ["cargo_tonnes", "portcalls"]:
        observed = daily[col].dropna()
        if observed.lt(0).any() or not np.isfinite(observed).all():
            raise ValueError(f"Invalid observed values in {col}")

    per_port = daily.groupby("port_id", sort=False)
    daily["cargo_7d"] = per_port.cargo_tonnes.transform(lambda s: s.rolling(7).sum())
    daily["calls_7d"] = per_port.portcalls.transform(lambda s: s.rolling(7).sum())
    daily["cargo_mean_28d"] = per_port.cargo_tonnes.transform(lambda s: s.rolling(28).mean())
    daily["target_7d"] = per_port.cargo_tonnes.transform(lambda s: s.rolling(7).sum().shift(-7))
    rows = daily.loc[daily.date.between(first_origin, last_target - pd.Timedelta(days=7))].copy()
    if rows.empty:
        raise ValueError("Test window has no complete calendar horizon")
    rows = rows.rename(columns={"date": "origin_date"}).merge(cohort, on="port_id", validate="many_to_one")
    for days, column in [(1, "target_start"), (7, "target_end")]:
        rows[column] = (rows.origin_date + pd.Timedelta(days=days)).dt.strftime("%Y-%m-%d")
    rows["origin_date"] = rows.origin_date.dt.strftime("%Y-%m-%d")
    rows["split"] = "test"
    no_history = rows[FEATURES].isna().any(axis=1)
    no_target = rows.target_7d.isna()
    excluded = rows.loc[no_history | no_target, KEYS].copy()
    excluded["incomplete_history"] = no_history.loc[excluded.index]
    excluded["incomplete_target"] = no_target.loc[excluded.index]
    columns = [*KEYS, "country_iso3", "activity_group", *FEATURES, "target_start", "target_end", "target_7d", "split"]
    return rows.loc[~(no_history | no_target), columns], excluded


def check_frozen_inputs(manifest, files):
    if manifest["status"] != "locked_before_test_scoring":
        raise ValueError("A frozen Task 5 manifest is required")
    for name, path in files.items():
        if sha256(path) != manifest["sha256"][name]:
            raise ValueError(f"Frozen inputs differ: {name} ({path})")
    for package, expected in manifest["packages"].items():
        actual = version(package)
        if actual != expected:
            raise ValueError(f"Install {package}=={expected}; version {actual} is active")


def forecast(train, test, manifest, handoff, model_script):
    # Estimators receive only the predictor columns at test time.
    inputs = test[FEATURES]
    rows = []

    def add(model, feature_set, raw):
        if len(raw) != len(test) or not np.isfinite(raw).all():
            raise ValueError(f"Invalid forecasts from {model}/{feature_set}")
        frame = test[[*KEYS, "country_iso3", "target_start", "target_end", "target_7d"]].rename(
            columns={"target_7d": "y_true"})
        frame = frame.assign(model=model, feature_set=feature_set, split="test", y_pred=np.maximum(raw, 0),
                             y_pred_raw=raw)
        rows.append(frame[[*FORECAST_COLUMNS, "y_pred_raw"]])
        print(f"Predicted {model}/{feature_set} on {len(frame):,} origins.", flush=True)

    for variant in manifest["baseline_variants"]:
        model, columns = variant["model"], variant["columns"]
        if model == "seasonal_naive":
            raw = inputs.cargo_7d.to_numpy()
        else:
            raw, _ = fit_regression(train, inputs, columns, quadratic=variant.get("quadratic", False))
        add(model, variant["feature_set"], raw)

    # The caller has checked this exact file against the model handoff hash.
    spec = importlib.util.spec_from_file_location("task3_frozen_models", model_script)
    model_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_module)
    from threadpoolctl import threadpool_limits

    with threadpool_limits(limits=2):
        for variant in handoff["chosen"]:
            model, feature_set = variant["model"], variant["feature_set"]
            raw, _ = model_module.fit_predict(model, variant["params"], handoff["feature_sets"][feature_set],
                                               train, inputs, handoff["seed"])
            add(model, feature_set, raw)
    return pd.concat(rows, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("results/task5_freeze.json"))
    parser.add_argument("--panel", type=Path, default=Path("data/da_xu_ly/ports_daily.csv"))
    parser.add_argument("--learning-table", type=Path, default=Path("data/learning_table.csv"))
    parser.add_argument("--model-handoff", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=Path("results/task5_test"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    files = {"experiment": root / "experiment.json", "panel": args.panel, "learning_table": args.learning_table,
             "ports": root / "results/task2_ports.csv", "baseline_code": root / "src/baselines.py",
             "feature_code": root / "src/features.py",
             "evaluator_code": root / "src/evaluate.py", "test_runner_code": Path(__file__),
             "model_code": args.model_handoff / "src/models.py",
             "model_config": args.model_handoff / "results/model_config.json"}
    try:
        if args.out_dir.exists():
            raise ValueError("Choose a new --out-dir to preserve the previous run")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        check_frozen_inputs(manifest, files)
        config = json.loads(files["experiment"].read_text(encoding="utf-8"))
        handoff = json.loads(files["model_config"].read_text(encoding="utf-8"))
        table = pd.read_csv(args.learning_table, dtype={"port_id": "string"},
                            parse_dates=["origin_date", "target_start", "target_end"])
        check_learning_table(table, config)
        train = table.loc[table.split.eq("train")].sort_values(KEYS).reset_index(drop=True)
        ports = pd.read_csv(files["ports"], dtype={"port_id": "string"})
        if set(train.port_id) != set(ports.loc[ports.selected, "port_id"]):
            raise ValueError("Training and frozen evaluation cohorts differ")
        test, excluded = build_test_windows(read_panel(args.panel), ports, config)
        if len(test) + len(excluded) != manifest["scheduled_port_origins"]:
            raise ValueError("Test calendar or cohort differs from the frozen plan")
        reference = reference_rows(test, config, "test")
        raw = forecast(train, test, manifest, handoff, files["model_code"])
        # Only changed rows are needed to reconstruct raw forecasts from the main export.
        clipped_rows = raw.loc[raw.y_pred_raw.lt(0),
                               ["model", "feature_set", *KEYS, "y_pred_raw", "y_pred"]]
        predictions = raw[FORECAST_COLUMNS]
        aligned, coverage = align_forecasts(predictions, reference, "test")
        metrics, errors = score(aligned, "all_eligible")
        overall = metrics.loc[metrics.group_type.eq("overall")].copy()
        naive = overall.loc[overall.model.eq("seasonal_naive"), "MAE"].item()
        overall["MAE_vs_naive_pct"] = 100 * (overall.MAE / naive - 1) if naive > 0 else np.nan
        overall["primary_comparison"] = [f"{model}/{fs}" in manifest["primary_comparison"]
                                         for model, fs in zip(overall.model, overall.feature_set)]
        compact = overall.sort_values(["primary_comparison", "MAE"], ascending=[False, True])

        args.out_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.out_dir.parent) as scratch:
            staged = Path(scratch) / "run"
            staged.mkdir()
            tables = {"test_reference.csv": test, "test_predictions.csv": predictions, "metrics.csv": metrics,
                      "overall_comparison.csv": compact, "coverage.csv": coverage,
                      "window_exclusions.csv": excluded, "highest_error_predictions.csv": errors,
                      "test_clipped_predictions.csv": clipped_rows}
            for name, frame in tables.items():
                frame.to_csv(staged / name, index=False, lineterminator="\n")
            record = {"status": "fixed_2026_test_comparison", "split": "test", "scope": "all_eligible",
                      "model_commit": manifest["model_commit"], "freeze_sha256": sha256(args.manifest),
                      "input_sha256": manifest["sha256"], "train_rows": len(train),
                      "evaluated_ports": reference.port_id.nunique(), "variants": len(coverage),
                      "scheduled_per_variant": len(test) + len(excluded), "evaluated_per_variant": len(test),
                      "excluded_per_variant": len(excluded), "zero_actual_per_variant": int(reference.y_true.eq(0).sum()),
                      "clipped_rows_across_variants": len(clipped_rows),
                      "target_start": reference.target_start.min(), "target_end": reference.target_end.max(),
                      "pool_ports": True, "refit_on_validation": False, "clipping": "nonnegative",
                      "python": platform.python_version(), "packages": manifest["packages"],
                      "output_sha256": {name: sha256(staged / name) for name in tables}}
            (staged / "evaluation_run.json").write_text(json.dumps(record, indent=2) + "\n",
                                                         encoding="utf-8", newline="\n")
            staged.rename(args.out_dir)
        print(compact[["model", "feature_set", "n_rows", "MAE", "RMSE", "WAPE_pct"]].to_string(index=False))
        print(f"Saved aligned holdout forecasts and evaluation to {args.out_dir}")
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
