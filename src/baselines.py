"""Fit four Task 2 baselines on training rows and evaluate validation only."""

import argparse
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from features import FEATURES, KEYS, sha256, validate_config

MODEL_FEATURES = {
    "seasonal_naive": "cargo_only",
    "linear_univariate": "cargo_only",
    "linear_multivariate": "all_three",
    "polynomial_degree2": "cargo_squared",
}


def fit_regression(train, validation, columns, quadratic=False):
    """OLS with an intercept; centring/scaling is fitted on training rows only."""
    x = train[columns].to_numpy(float)
    v = validation[columns].to_numpy(float)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1
    x, v = (x - mean) / scale, (v - mean) / scale
    if quadratic:
        # [1, z, z^2] spans the same degree-2 polynomial as [1, cargo, cargo^2].
        x, v = np.column_stack([x, x ** 2]), np.column_stack([v, v ** 2])
    design = np.column_stack([np.ones(len(x)), x])
    coef, _, rank, _ = np.linalg.lstsq(design, train.target_7d.to_numpy(float), rcond=None)
    predicted = np.column_stack([np.ones(len(v)), v]) @ coef
    if not np.isfinite(predicted).all():
        raise ValueError("Nonfinite regression prediction")
    return predicted, {"input_columns": columns, "quadratic": quadratic,
        "training_mean": mean.tolist(), "training_scale": scale.tolist(),
        "coefficients": coef.tolist(), "rank": int(rank), "training_rows": len(train)}


def check_learning_table(table, config):
    start, a, b = validate_config(config)
    required = {*KEYS, "country_iso3", "activity_group", *FEATURES,
                "target_start", "target_end", "target_7d", "split"}
    if required - set(table) or table.empty:
        raise ValueError("Incomplete learning-table schema or empty table")
    if table.duplicated(KEYS).any() or table[list(required)].isna().any().any():
        raise ValueError("Duplicate keys or missing learning-table values")
    if not table.split.isin(["train", "validation"]).all():
        raise ValueError("Baseline runner accepts train and validation only; test is reserved")
    if not table.origin_date.eq(table.origin_date.dt.normalize()).all():
        raise ValueError("Expected daily midnight origin dates")
    if not table.origin_date.ge(start + pd.Timedelta(days=27)).all():
        raise ValueError("Origin precedes the required 28-day training history")
    values = table[[*FEATURES, "target_7d"]].to_numpy(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Invalid feature or target values")
    if not table.target_start.eq(table.origin_date + pd.Timedelta(days=1)).all() or not table.target_end.eq(
            table.origin_date + pd.Timedelta(days=7)).all():
        raise ValueError("Target dates must be origin+1 through origin+7")
    train = table.loc[table.split.eq("train")]
    val = table.loc[table.split.eq("validation")]
    if train.empty or val.empty or not train.target_end.le(a).all() or not (
            val.origin_date.ge(a) & val.target_end.le(b)).all():
        raise ValueError("Empty split or target crossing a split boundary")
    if not set(val.port_id).issubset(set(train.port_id)):
        raise ValueError("Validation contains ports absent from training")


def predict_baselines(table, config):
    check_learning_table(table, config)
    train = table.loc[table.split.eq("train")].sort_values(KEYS)
    val = table.loc[table.split.eq("validation")].sort_values(KEYS)
    predictions = {"seasonal_naive": val.cargo_7d.to_numpy(float)}
    fits = {"seasonal_naive": {"rule": "last_seven_calendar_days_cargo_total"}}
    for name, cols, quadratic in [
        ("linear_univariate", ["cargo_7d"], False),
        ("linear_multivariate", FEATURES, False),
        ("polynomial_degree2", ["cargo_7d"], True),
    ]:
        predictions[name], fits[name] = fit_regression(train, val, cols, quadratic)
    rows = []
    for model, values in predictions.items():
        f = val[["port_id", "country_iso3", "origin_date", "target_start", "target_end",
                 "target_7d", "activity_group"]].rename(columns={"target_7d": "y_true"}).copy()
        f["model"], f["feature_set"], f["split"], f["y_pred"] = model, MODEL_FEATURES[model], "validation", values
        rows.append(f)
    columns = ["model", "feature_set", "split", "port_id", "country_iso3", "origin_date",
               "target_start", "target_end", "y_true", "y_pred", "activity_group"]
    return pd.concat(rows, ignore_index=True)[columns], fits


def score_predictions(predictions):
    """Pooled MAE/RMSE/WAPE plus per-port mean MAE and row counts."""
    rows = []
    for model, f in predictions.groupby("model", sort=False):
        error = f.y_pred - f.y_true
        denom = f.y_true.sum()
        rows.append({"model": model, "feature_set": f.feature_set.iloc[0], "split": "validation",
            "n_rows": len(f), "n_ports": f.port_id.nunique(), "MAE": error.abs().mean(),
            "RMSE": np.sqrt((error ** 2).mean()),
            "WAPE_pct": 100 * error.abs().sum() / denom if denom else np.nan,
            "macro_port_MAE": error.abs().groupby(f.port_id).mean().mean(),
            "negative_predictions": int(f.y_pred.lt(0).sum())})
    return pd.DataFrame(rows)


def export_baselines(table, config, results_dir=Path("results"), clipping=None):
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    raw, fits = predict_baselines(table, config)
    if clipping is None:
        clipping = "nonnegative" if config.get("clip_negative_predictions") is True else "none"
    if clipping not in ["none", "nonnegative"]:
        raise ValueError("clipping must be none or nonnegative")
    variants, metrics = {}, []
    for rule in ["none", "nonnegative"]:
        f = raw.copy()
        if rule == "nonnegative":
            f["y_pred"] = f.y_pred.clip(lower=0)
        f["clipping"] = rule
        variants[rule] = f
        scores = score_predictions(f)
        scores["clipping"] = rule
        scores["working_output"] = rule == clipping
        metrics.append(scores)
    for rule, f in variants.items():
        f.to_csv(results_dir / f"baseline_{rule}_predictions.csv", index=False,
                 date_format="%Y-%m-%d", lineterminator="\n")
    variants[clipping].to_csv(results_dir / "validation_predictions.csv", index=False,
                             date_format="%Y-%m-%d", lineterminator="\n")
    scores = pd.concat(metrics, ignore_index=True)
    scores.to_csv(results_dir / "baseline_metrics.csv", index=False, lineterminator="\n")
    (results_dir / "baseline_fits.json").write_text(json.dumps(fits, indent=2) + "\n", encoding="utf-8")
    best = scores.loc[scores.working_output].sort_values("MAE").iloc[0]
    lines = ["# Task 2 validation results", "", "Validation only. The shared cohort and clipping rule still require team agreement.",
             "", f"Working output clipping: {clipping}. Both raw and nonnegative variants are exported separately.",
             "", "| Model | Clipping | Rows | MAE tonnes | RMSE tonnes | WAPE percent |",
             "|---|---|---:|---:|---:|---:|"]
    for row in scores.itertuples():
        lines.append(f"| {row.model} | {row.clipping} | {row.n_rows:,} | {row.MAE:,.2f} | {row.RMSE:,.2f} | {row.WAPE_pct:.4f} |")
    lines += ["", f"Lowest validation MAE in the working output: {best['model']}. This is not a test conclusion.",
              "", "All four models use identical port-origin rows. Negative raw forecasts are disclosed; no test scores are generated.",
              "Daily seven-day target windows overlap. Do not sum them as independent weekly cargo totals.", ""]
    (results_dir / "baseline_validation.md").write_text("\n".join(lines), encoding="utf-8")
    print(scores[["model", "clipping", "n_rows", "MAE", "RMSE", "WAPE_pct"]].to_string(index=False))
    return variants[clipping], scores, fits


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--table", type=Path, default=Path("data/learning_table.csv"))
    p.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    p.add_argument("--results-dir", type=Path, default=Path("results"))
    p.add_argument("--clipping", choices=["none", "nonnegative"], default=None)
    a = p.parse_args()
    if not a.table.is_file():
        p.error(f"Missing learning table: {a.table}. Obtain Dinh's feature export or run src/features.py first")
    table = pd.read_csv(a.table, parse_dates=["origin_date", "target_start", "target_end"],
                        dtype={"port_id": "string", "country_iso3": "string"})
    config = json.loads(a.experiment.read_text(encoding="utf-8"))
    predictions, _, _ = export_baselines(table, config, a.results_dir, a.clipping)
    record = {
        "status": "baseline_validation_run; shared_rule_freeze_pending",
        "test_scored": False,
        "learning_table_sha256": sha256(a.table),
        "experiment_sha256": sha256(a.experiment),
        "code_sha256": {name: sha256(Path(__file__).with_name(name))
                        for name in ["features.py", "baselines.py"]},
        "train_rows": int(table.split.eq("train").sum()),
        "validation_rows_per_model": int(table.split.eq("validation").sum()),
        "ports": int(predictions.port_id.nunique()),
        "clipping_in_working_output": predictions.clipping.iloc[0],
        "clipping_configured": config.get("clip_negative_predictions"),
        "cutoffs": {k: config[k] for k in
                    ["train_start", "train_end", "validation_end", "test_end"]},
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__},
        "output_sha256": {name: sha256(a.results_dir / name) for name in [
            "validation_predictions.csv", "baseline_none_predictions.csv",
            "baseline_nonnegative_predictions.csv", "baseline_metrics.csv", "baseline_fits.json"]},
    }
    (a.results_dir / "baseline_run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
