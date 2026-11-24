"""Task 3: Random Forest and Histogram Gradient Boosting on the Task 2 learning table.

Both models share one interface: `fit_predict(model, params, columns, train, validation, seed)`.
Fitting uses training rows only. Settings are chosen by validation MAE of the common
nonnegative rule max(raw, 0). Test rows are never read: the learning table contains
train/validation only and the loader rejects any other split.

Run from the repository root:
    python src/models.py --table data/learning_table.csv --keys results/task2_validation_keys.csv \
        --out-dir results

Prediction files are named model_*_predictions.csv so they never overwrite the Task 2
baseline file results/validation_predictions.csv.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

SEED = 42
TARGET = "target_7d"
KEY = ["port_id", "origin_date"]

FEATURE_SETS = {
    "cargo_only": ["cargo_7d"],
    "cargo_calls": ["cargo_7d", "calls_7d"],
    "cargo_mean28": ["cargo_7d", "cargo_mean_28d"],
    "all_three": ["cargo_7d", "calls_7d", "cargo_mean_28d"],
}

GRIDS = {
    "random_forest": {
        "n_estimators": [50, 100],
        "max_depth": [6, 8, 14],
        "min_samples_leaf": [50, 100, 300],
    },
    "hist_gradient_boosting": {
        "loss": ["squared_error", "absolute_error"],
        "learning_rate": [0.05, 0.1],
        "max_iter": [100, 300],
        "max_leaf_nodes": [15, 63],
        "min_samples_leaf": [20, 1000],
    },
}

EXPORT_COLUMNS = [
    "model", "feature_set", "split", "port_id", "country_iso3", "origin_date",
    "target_start", "target_end", "y_true", "y_pred",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_table(path: Path) -> pd.DataFrame:
    """Read the learning table and refuse anything except train/validation."""
    table = pd.read_csv(path)
    bad = set(table["split"]) - {"train", "validation"}
    if bad:
        raise ValueError(f"Unexpected split values {sorted(bad)}; test must stay reserved.")
    if table.duplicated(KEY).any():
        raise ValueError("Duplicate (port_id, origin_date) keys in the learning table.")
    needed = {"cargo_7d", "calls_7d", "cargo_mean_28d", TARGET, "country_iso3",
              "target_start", "target_end"}
    missing = needed - set(table.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    cols = ["cargo_7d", "calls_7d", "cargo_mean_28d", TARGET]
    if table[cols].isna().any().any():
        raise ValueError("Learning table must contain complete rows only.")
    return table


def check_keys(validation: pd.DataFrame, keys_path: Path) -> str:
    """Validation rows must equal the frozen Task 2 key set exactly."""
    keys = pd.read_csv(keys_path)
    a = validation[["port_id", "origin_date", "target_start", "target_end"]]
    a = a.sort_values(KEY).reset_index(drop=True)
    b = keys.sort_values(KEY).reset_index(drop=True)[a.columns]
    if not a.equals(b):
        raise ValueError("Validation rows differ from results/task2_validation_keys.csv.")
    return sha256(keys_path)


def make_model(model: str, params: dict, seed: int = SEED):
    if model == "random_forest":
        return RandomForestRegressor(
            criterion="squared_error", max_features=1.0, bootstrap=True,
            n_jobs=2, random_state=seed, **params,
        )
    if model == "hist_gradient_boosting":
        # early_stopping=False: sklearn's automatic holdout is a random split of
        # time-ordered, overlapping rows, which would leak. The iteration count is
        # tuned on the chronological validation split instead.
        return HistGradientBoostingRegressor(
            early_stopping=False, random_state=seed, **params,
        )
    raise ValueError(f"Unknown model {model}")


def fit_predict(model, params, columns, train, validation, seed=SEED):
    """Fit on training rows only; return raw validation predictions and fit seconds."""
    start = time.perf_counter()
    est = make_model(model, params, seed)
    est.fit(train[columns].to_numpy(), train[TARGET].to_numpy())
    pred = est.predict(validation[columns].to_numpy())
    return pred, time.perf_counter() - start


def metrics(y_true, y_pred) -> dict:
    err = y_pred - y_true
    total = float(np.sum(y_true))
    return {
        "MAE": float(np.mean(np.abs(err))),
        "RMSE": float(np.sqrt(np.mean(err ** 2))),
        "WAPE_pct": float(100 * np.sum(np.abs(err)) / total) if total > 0 else float("nan"),
        "mean_bias": float(np.mean(err)),
        "negative_predictions": int(np.sum(y_pred < 0)),
    }


def tune(train, validation, models=("random_forest", "hist_gradient_boosting"), log=print):
    """Return (candidate records, best[(model, feature_set)] = (params, raw predictions))."""
    y = validation[TARGET].to_numpy()
    records, best = [], {}
    for model in models:
        grid = GRIDS[model]
        names = list(grid)
        combos = [dict(zip(names, v)) for v in itertools.product(*grid.values())]
        for fs, cols in FEATURE_SETS.items():
            for i, params in enumerate(combos):
                pred, seconds = fit_predict(model, params, cols, train, validation)
                raw = metrics(y, pred)
                clipped = metrics(y, np.maximum(pred, 0.0))
                rec = {
                    "model": model, "feature_set": fs, "candidate": i, **params,
                    "n_train": len(train), "n_validation": len(validation),
                    "fit_predict_seconds": round(seconds, 2),
                    "MAE_nonnegative": clipped["MAE"], "RMSE_nonnegative": clipped["RMSE"],
                    "WAPE_pct_nonnegative": clipped["WAPE_pct"],
                    "MAE_raw": raw["MAE"], "RMSE_raw": raw["RMSE"],
                    "WAPE_pct_raw": raw["WAPE_pct"],
                    "negative_predictions_raw": raw["negative_predictions"],
                }
                records.append(rec)
                key = (model, fs)
                if key not in best or clipped["MAE"] < best[key][2]:
                    best[key] = (params, pred, clipped["MAE"])
                log(f"{model:24s} {fs:13s} {i + 1}/{len(combos)} "
                    f"MAE={clipped['MAE']:.1f} ({seconds:.1f}s)")
    return records, best


def export(validation, best, out_dir: Path):
    """Write one file per clipping variant in the protocol schema."""
    base = validation[["port_id", "country_iso3", "origin_date", "target_start", "target_end"]]
    y = validation[TARGET].to_numpy()
    frames = {"none": [], "nonnegative": []}
    for (model, fs), (params, pred, _) in best.items():
        for rule, p in (("none", pred), ("nonnegative", np.maximum(pred, 0.0))):
            f = base.copy()
            f.insert(0, "feature_set", fs)
            f.insert(0, "model", model)
            f.insert(2, "split", "validation")
            f["y_true"], f["y_pred"] = y, p
            frames[rule].append(f[EXPORT_COLUMNS])
    paths = {
        "nonnegative": out_dir / "model_validation_predictions.csv",
        "none": out_dir / "model_none_predictions.csv",
    }
    for rule, parts in frames.items():
        out = pd.concat(parts, ignore_index=True)
        dup = out.duplicated(["model", "feature_set", "port_id", "origin_date"])
        if dup.any():
            raise ValueError("Duplicate prediction keys in export.")
        out.to_csv(paths[rule], index=False)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", type=Path, default=Path("data/learning_table.csv"))
    ap.add_argument("--keys", type=Path, default=Path("results/task2_validation_keys.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("results"))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    table = load_table(args.table)
    train = table[table["split"] == "train"].reset_index(drop=True)
    validation = table[table["split"] == "validation"].reset_index(drop=True)
    keys_hash = check_keys(validation, args.keys)

    t0 = time.perf_counter()
    records, best = tune(train, validation)
    total_seconds = time.perf_counter() - t0

    candidates = pd.DataFrame(records)
    candidates.to_csv(args.out_dir / "model_candidates.csv", index=False)
    paths = export(validation, best, args.out_dir)

    y = validation[TARGET].to_numpy()
    chosen, rows = [], []
    for (model, fs), (params, pred, _) in best.items():
        for rule, p in (("none", pred), ("nonnegative", np.maximum(pred, 0.0))):
            rows.append({"model": model, "feature_set": fs, "split": "validation",
                         "n_rows": len(y), "n_ports": validation["port_id"].nunique(),
                         "clipping": rule, **metrics(y, p)})
        chosen.append({"model": model, "feature_set": fs, "params": params})
    pd.DataFrame(rows).to_csv(args.out_dir / "model_validation_metrics.csv", index=False)

    config = {
        "status": "validation_only_test_not_scored",
        "seed": SEED,
        "selection_metric": "validation_MAE_of_nonnegative_predictions",
        "prediction_rule": "max(raw_prediction, 0) for the common comparison; raw kept as sensitivity",
        "target": TARGET,
        "feature_sets": FEATURE_SETS,
        "grids": GRIDS,
        "fixed_settings": {
            "random_forest": {"criterion": "squared_error", "max_features": 1.0, "bootstrap": True},
            "hist_gradient_boosting": {"early_stopping": False},
        },
        "chosen": chosen,
        "rows": {"train": len(train), "validation": len(validation),
                 "ports": int(validation["port_id"].nunique())},
        "total_tuning_seconds": round(total_seconds, 1),
        "refit_before_test": False,
        "hashes": {"learning_table_sha256": sha256(args.table),
                   "validation_keys_sha256": keys_hash,
                   "models_py_sha256": sha256(Path(__file__))},
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "scikit_learn": sklearn.__version__},
        "outputs": {k: str(v) for k, v in paths.items()},
    }
    (args.out_dir / "model_config.json").write_text(json.dumps(config, indent=2, default=str))
    print(pd.DataFrame(rows).query("clipping == 'nonnegative'")
          [["model", "feature_set", "MAE", "RMSE", "WAPE_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
