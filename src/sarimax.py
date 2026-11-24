"""Task 4 extension: per-port SARIMA on a training-selected subset (validation only).

Scope and rules
- Subset: ports in the training-defined `high` activity group of the Task 2 learning table.
- Each port series is fitted once on observations through 2024-12-31 (training only), with the
  order chosen by training AIC from a small fixed candidate list. Parameters are not refitted
  during validation; the observed history is appended day by day (`append(refit=False)`).
- At origin t the forecast uses observations through t only. The seven daily forecasts are
  summed to a seven-day total and multiplied back by the port's training mean scale
  (the series is divided by that scale before fitting).
- Observations after 2025-12-31 are dropped before anything is computed; test is not scored.
- No exogenous (oil) series is used. See docs/extension_decision.md for why SARIMAX is no-go.

Run from the repository root:
    python src/sarimax.py --panel data/da_xu_ly/ports_daily.csv --table data/learning_table.csv \
        --out-dir results
"""
from __future__ import annotations

import argparse
import json
import platform
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels
from statsmodels.tsa.statespace.sarimax import SARIMAX

TRAIN_END = "2024-12-31"
VALID_END = "2025-12-31"
HORIZON = 7
ORDERS = [
    ((1, 0, 0), (1, 0, 0, 7)),
    ((1, 0, 1), (1, 0, 1, 7)),
    ((2, 0, 1), (1, 0, 1, 7)),
]
MODEL = "sarima"
FEATURE_SET = "cargo_history"
EXPORT_COLUMNS = [
    "model", "feature_set", "split", "port_id", "country_iso3", "origin_date",
    "target_start", "target_end", "y_true", "y_pred",
]


def forecast_port(args):
    """Fit on training data and forecast each validation origin. Returns (port_id, frame, info)."""
    port_id, series, origins = args
    warnings.filterwarnings("ignore")
    start = time.perf_counter()
    train = series[:TRAIN_END]
    scale = float(train.mean())
    info = {"port_id": port_id, "train_mean": scale, "status": "ok", "order": None,
            "seasonal_order": None, "train_aic": None, "seconds": None, "converged": None}
    if not np.isfinite(scale) or scale <= 0:
        info["status"] = "skipped_zero_training_mean"
        return port_id, None, info
    y = train / scale
    best = None
    for order, seasonal in ORDERS:
        try:
            res = SARIMAX(y, order=order, seasonal_order=seasonal, trend="c",
                          enforce_stationarity=False, enforce_invertibility=False
                          ).fit(disp=False, maxiter=100)
        except Exception:
            continue
        if np.isfinite(res.aic) and (best is None or res.aic < best[0]):
            best = (res.aic, order, seasonal, res)
    if best is None:
        info["status"] = "failed_all_candidates"
        return port_id, None, info
    aic, order, seasonal, res = best
    info.update(order=list(order), seasonal_order=list(seasonal), train_aic=float(aic),
                converged=bool(res.mle_retvals.get("converged", False)))
    future = series[pd.Timestamp(TRAIN_END) + pd.Timedelta(days=1):VALID_END] / scale
    preds, cur = [], res
    try:
        for origin in origins:
            preds.append(float(cur.forecast(HORIZON).sum()))
            nxt = pd.Timestamp(origin) + pd.Timedelta(days=1)
            cur = cur.append(future[[nxt]], refit=False)
    except Exception as exc:  # keep the failure visible; the port is excluded
        info["status"] = f"failed_forecast:{type(exc).__name__}"
        return port_id, None, info
    frame = pd.DataFrame({"port_id": port_id, "origin_date": origins,
                          "y_pred_raw": np.array(preds) * scale})
    info["seconds"] = round(time.perf_counter() - start, 2)
    return port_id, frame, info


def metrics(y_true, y_pred):
    err = y_pred - y_true
    total = float(np.sum(y_true))
    return {"MAE": float(np.mean(np.abs(err))), "RMSE": float(np.sqrt(np.mean(err ** 2))),
            "WAPE_pct": float(100 * np.sum(np.abs(err)) / total) if total > 0 else float("nan")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, default=Path("data/da_xu_ly/ports_daily.csv"))
    ap.add_argument("--table", type=Path, default=Path("data/learning_table.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("results"))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--max-ports", type=int, default=None, help="debug only")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    table = pd.read_csv(args.table)
    if set(table["split"]) - {"train", "validation"}:
        raise ValueError("Test rows must not be present.")
    val = table[table["split"] == "validation"]
    # training-defined subset: the `high` activity group (cut from training active share)
    group = table.drop_duplicates("port_id").set_index("port_id")["activity_group"]
    ports = sorted(group[group == "high"].index)
    if args.max_ports:
        ports = ports[: args.max_ports]
    origins = sorted(val["origin_date"].unique())

    panel = pd.read_csv(args.panel, parse_dates=["date"], usecols=["date", "port_id", "cargo_tonnes"])
    panel = panel[panel["date"] <= VALID_END]  # nothing after validation enters any computation
    jobs = []
    for pid in ports:
        s = panel[panel["port_id"] == pid].set_index("date")["cargo_tonnes"].asfreq("D")
        jobs.append((pid, s, origins))

    t0 = time.perf_counter()
    with Pool(args.workers) as pool:
        results = pool.map(forecast_port, jobs)
    total_seconds = time.perf_counter() - t0

    infos = pd.DataFrame([r[2] for r in results])
    infos.to_csv(args.out_dir / "extension_port_fits.csv", index=False)
    frames = [r[1] for r in results if r[1] is not None]
    pred = pd.concat(frames, ignore_index=True)
    keys = val[["port_id", "country_iso3", "origin_date", "target_start", "target_end", "target_7d"]]
    merged = keys.merge(pred, on=["port_id", "origin_date"], how="inner")
    merged = merged.rename(columns={"target_7d": "y_true"})
    if merged.duplicated(["port_id", "origin_date"]).any():
        raise ValueError("Duplicate prediction keys.")

    out = {}
    for rule, col in (("nonnegative", np.maximum(merged["y_pred_raw"], 0.0)), ("none", merged["y_pred_raw"])):
        f = merged.copy()
        f["y_pred"] = col
        f["model"], f["feature_set"], f["split"] = MODEL, FEATURE_SET, "validation"
        f = f[EXPORT_COLUMNS]
        path = args.out_dir / ("extension_predictions.csv" if rule == "nonnegative"
                               else "extension_none_predictions.csv")
        f.to_csv(path, index=False)
        out[rule] = (path, f)

    summary = {
        "status": "validation_only_test_not_scored",
        "model": MODEL,
        "subset_rule": "ports in the training-defined high activity group (training active share >= 2/3)",
        "ports_requested": len(ports),
        "ports_fitted": int(len(frames)),
        "ports_excluded": infos.loc[infos["status"] != "ok", ["port_id", "status"]].to_dict("records"),
        "origins_per_port": len(origins),
        "rows": int(len(merged)),
        "candidate_orders": [[list(o), list(s)] for o, s in ORDERS],
        "order_selection": "training AIC",
        "refit_during_validation": False,
        "exogenous_variables": "none",
        "prediction_rule": "max(raw, 0); raw kept in extension_none_predictions.csv",
        "total_seconds": round(total_seconds, 1),
        "workers": args.workers,
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "statsmodels": statsmodels.__version__},
        "metrics_nonnegative": metrics(merged["y_true"].to_numpy(), out["nonnegative"][1]["y_pred"].to_numpy()),
        "metrics_raw": metrics(merged["y_true"].to_numpy(), out["none"][1]["y_pred"].to_numpy()),
    }
    (args.out_dir / "extension_run.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in ("ports_requested", "ports_fitted", "rows",
                                              "total_seconds", "metrics_nonnegative")}, indent=2))


if __name__ == "__main__":
    main()
