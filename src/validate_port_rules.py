"""Task 1 eligibility sensitivity for joint Task 2 review; validation only.

Uses the shared protocol's three features and pooled linear regression as a
fixed diagnostic, not a replacement for Task 2's production learning table.
No test-period measurements enter features, labels, fitting or scoring.
"""

import argparse
import copy
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from prepare_data import select_ports, sha256, write_csv, write_json, markdown_table


FEATURES = ["cargo_7d", "calls_7d", "cargo_mean_28d"]
PREDICTION_COLUMNS = ["model", "feature_set", "split", "port_id", "country_iso3",
                      "origin_date", "target_start", "target_end", "y_true", "y_pred"]
CANDIDATES = {"coverage_only": 0.0, "active_20pct": 0.2}


def validation_table(panel, experiment):
    """Construct protocol windows within ports, discarding test data first."""
    start = pd.Timestamp(experiment["train_start"])
    a = pd.Timestamp(experiment["train_end"])
    b = pd.Timestamp(experiment["validation_end"])
    frame = panel.loc[panel.date.le(b)].sort_values(["port_id", "date"]).copy()
    if frame.duplicated(["port_id", "date"]).any():
        raise ValueError("Duplicate panel keys")
    gaps = frame.groupby("port_id")["date"].diff().dropna()
    if not gaps.eq(pd.Timedelta(days=1)).all():
        raise ValueError("Reindex the panel to daily calendars before calculating windows")
    cargo = frame.groupby("port_id")["cargo_tonnes"]
    frame["cargo_7d"] = cargo.transform(lambda s: s.rolling(7, min_periods=7).sum())
    frame["cargo_mean_28d"] = cargo.transform(lambda s: s.rolling(28, min_periods=28).mean())
    frame["calls_7d"] = frame.groupby("port_id")["portcalls"].transform(lambda s: s.rolling(7, min_periods=7).sum())
    frame["y_true"] = cargo.transform(lambda s: s.rolling(7, min_periods=7).sum().shift(-7))
    frame["target_start"] = frame.date + pd.Timedelta(days=1)
    frame["target_end"] = frame.date + pd.Timedelta(days=7)
    frame["split"] = np.select(
        [frame.date.ge(start) & frame.target_end.le(a), frame.date.ge(a) & frame.target_end.le(b)],
        ["train", "validation"], default="excluded",
    )
    frame["window_complete"] = frame[[*FEATURES, "y_true"]].notna().all(axis=1)
    frame["exclusion_reason"] = np.select(
        [frame.date.lt(start), frame.date.eq(b), frame.target_end.gt(b), frame.split.eq("excluded"),
         frame[FEATURES].isna().any(axis=1), frame.y_true.isna()],
        ["before_training_start", "origin_reserved_for_test", "target_beyond_validation_end",
         "target_crosses_train_validation_boundary", "incomplete_past_window", "incomplete_future_target"],
        default="",
    )
    return frame


def fit_linear(training, evaluation):
    """Train-fitted scaling and stable least squares, with an intercept."""
    x = training[FEATURES].to_numpy(dtype=float)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1.0
    design = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    coefficients, _, rank, singular = np.linalg.lstsq(design, training.y_true.to_numpy(dtype=float), rcond=None)
    future = np.column_stack([np.ones(len(evaluation)), (evaluation[FEATURES].to_numpy(dtype=float) - mean) / scale])
    prediction = future @ coefficients
    if not np.isfinite(prediction).all():
        raise ValueError("Non-finite linear predictions")
    return prediction, {"feature_order": FEATURES, "training_mean": mean.tolist(), "training_scale": scale.tolist(),
                        "coefficients_intercept_then_scaled_features": coefficients.tolist(),
                        "design_rank": int(rank), "design_columns": design.shape[1],
                        "condition_number": float(singular[0] / singular[-1]) if singular[-1] > 0 else None,
                        "clip_negative_predictions": False}


def metrics(frame):
    if frame.empty:
        raise ValueError("Cannot score an empty common evaluation set")
    error = frame.y_pred.to_numpy(dtype=float) - frame.y_true.to_numpy(dtype=float)
    absolute = np.abs(error)
    denominator = float(frame.y_true.sum())
    per_port = pd.Series(absolute, index=frame.index).groupby(frame.port_id).mean()
    return {"n_rows": len(frame), "n_ports": int(frame.port_id.nunique()),
            "MAE": float(absolute.mean()), "RMSE": float(np.sqrt(np.mean(error ** 2))),
            "WAPE_pct": float(100 * absolute.sum() / denominator) if denominator else None,
            "macro_port_MAE": float(per_port.mean()), "zero_actual_windows": int(frame.y_true.eq(0).sum()),
            "negative_predictions": int(frame.y_pred.lt(0).sum()), "actual_tonnes_sum": denominator}


def candidate_lists(panel, experiment):
    selections = {}
    for name, threshold in CANDIDATES.items():
        config = copy.deepcopy(experiment)
        config["port_selection"]["status"] = "candidate_for_validation"
        config["port_selection"]["min_active_share"] = threshold
        selections[name] = select_ports(panel, config)
    return selections


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=Path("data/ports_daily.csv"))
    parser.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    started = time.perf_counter()
    experiment = json.loads(args.experiment.read_text(encoding="utf-8"))
    audit = json.loads((args.results_dir / "data_audit.json").read_text(encoding="utf-8"))
    if sha256(args.panel) != audit["panel_sha256"] or experiment["data_snapshot_sha256"] != audit["data_snapshot_sha256"]:
        raise ValueError("Panel, preparation audit and experiment provenance must match")
    if experiment["port_selection"]["min_cargo_coverage"] != 1.0:
        raise ValueError("This diagnostic compares two candidates with complete training cargo coverage")
    panel = pd.read_csv(args.panel, parse_dates=["date"], dtype={"port_id": "string", "country_iso3": "string"})
    selections = candidate_lists(panel, experiment)
    sets = {name: set(s.loc[s.selected, "port_id"]) for name, s in selections.items()}
    common_ports = set.intersection(*sets.values())
    if not common_ports:
        raise ValueError("No common eligible ports")
    table = validation_table(panel, experiment)
    valid = table.window_complete & table.split.eq("validation")
    evaluation = table.loc[valid & table.port_id.isin(common_ports)].copy()
    evaluation = evaluation.sort_values(["port_id", "date"]).reset_index(drop=True)
    if evaluation.empty or evaluation.duplicated(["port_id", "date"]).any():
        raise ValueError("Common evaluation keys must be nonempty and unique")
    common_keys = evaluation[["port_id", "country_iso3", "date", "target_start", "target_end"]].rename(columns={"date": "origin_date"})
    write_csv(common_keys, args.results_dir / "eligibility_validation_keys.csv")
    key_hash = sha256(args.results_dir / "eligibility_validation_keys.csv")
    exclusions = table.loc[table.exclusion_reason.ne("") | (valid & ~table.port_id.isin(common_ports)),
                           ["port_id", "country_iso3", "date", "split", "exclusion_reason"]].copy()
    exclusions.loc[exclusions.exclusion_reason.eq(""), "exclusion_reason"] = "outside_common_training_eligibility_set"
    exclusions = exclusions.rename(columns={"date": "origin_date"})
    write_csv(exclusions, args.results_dir / "eligibility_origin_exclusions.csv")
    excluded_summary = exclusions.groupby(["split", "exclusion_reason"], sort=True).size().rename("rows").reset_index()
    write_csv(excluded_summary, args.results_dir / "eligibility_exclusion_summary.csv")
    training = table.loc[table.split.eq("train") & table.window_complete].copy()
    scores, breakdowns, settings, origin_counts, training_exclusions = [], [], {}, [], []
    group_map = selections["coverage_only"].set_index("port_id")["activity_group"]
    for rule_name, included in sets.items():
        candidate_training = training.loc[training.port_id.isin(included)]
        if candidate_training.empty:
            raise ValueError(f"No training samples for {rule_name}")
        rejected = training.loc[~training.port_id.isin(included), ["port_id", "country_iso3", "date"]].copy()
        rejected = rejected.rename(columns={"date": "origin_date"})
        rejected["eligibility_rule"] = rule_name
        rejected["exclusion_reason"] = "port_failed_training_eligibility"
        training_exclusions.append(rejected)
        predicted, settings[rule_name] = fit_linear(candidate_training, evaluation)
        origin_counts.append({"eligibility_rule": rule_name, "eligible_ports": len(included),
                              "complete_training_rows_before_port_rule": len(training),
                              "training_rows": len(candidate_training),
                              "training_rows_excluded_by_port_rule": len(training) - len(candidate_training),
                              "complete_validation_rows_before_common_set": int(valid.sum()),
                              "common_validation_rows": len(evaluation), "common_validation_ports": len(common_ports),
                              "validation_rows_excluded_by_common_set": int(valid.sum()) - len(evaluation)})
        outputs = []
        for model, feature_set, predictions in [
            ("multivariate_linear_regression", "all_three", predicted),
            ("seasonal_naive", "cargo_only", evaluation.cargo_7d.to_numpy(dtype=float)),
        ]:
            scored = evaluation[["port_id", "country_iso3", "date", "target_start", "target_end", "y_true"]].copy()
            scored = scored.rename(columns={"date": "origin_date"})
            scored["model"], scored["feature_set"], scored["split"], scored["y_pred"] = model, feature_set, "validation", predictions
            scores.append({"eligibility_rule": rule_name, "model": model, **metrics(scored)})
            scored["activity_group"] = scored.port_id.map(group_map)
            for group_type, column in [("country", "country_iso3"), ("activity", "activity_group"), ("port", "port_id")]:
                for group, sample in scored.groupby(column, sort=True):
                    breakdowns.append({"eligibility_rule": rule_name, "model": model, "group_type": group_type,
                                       "group_value": str(group), **metrics(sample)})
            outputs.append(scored[PREDICTION_COLUMNS])
        write_csv(pd.concat(outputs, ignore_index=True), args.results_dir / f"eligibility_validation_predictions_{rule_name}.csv")
    score_table = pd.DataFrame(scores)
    write_csv(score_table, args.results_dir / "eligibility_validation_metrics.csv")
    write_csv(pd.DataFrame(breakdowns), args.results_dir / "eligibility_validation_breakdown.csv")
    write_csv(pd.DataFrame(origin_counts), args.results_dir / "eligibility_origin_counts.csv")
    write_csv(pd.concat(training_exclusions, ignore_index=True), args.results_dir / "eligibility_training_exclusions.csv")
    country_retention = []
    for name, selection in selections.items():
        for country, sample in selection.groupby("country_iso3", sort=True):
            country_retention.append({"eligibility_rule": name, "country_iso3": country, "source_ports": len(sample),
                                      "retained_ports": int(sample.selected.sum()),
                                      "common_evaluation_ports": int(sample.port_id.isin(common_ports).sum())})
    write_csv(pd.DataFrame(country_retention), args.results_dir / "eligibility_country_retention.csv")
    ranking = score_table.loc[score_table.model.eq("multivariate_linear_regression")].sort_values(["MAE", "eligibility_rule"])
    recommended = str(ranking.iloc[0].eligibility_rule)
    linear = score_table.loc[score_table.model.eq("multivariate_linear_regression")].set_index("eligibility_rule")
    mae_improvement = float(linear.loc["coverage_only", "MAE"] - linear.loc["active_20pct", "MAE"])
    relative_improvement = 100 * mae_improvement / float(linear.loc["coverage_only", "MAE"])
    rmse_change = float(linear.loc["active_20pct", "RMSE"] - linear.loc["coverage_only", "RMSE"])
    used_config = {k: experiment[k] for k in ["train_start", "train_end", "validation_end", "test_end", "data_snapshot_sha256"]}
    used_config.update(candidates=CANDIDATES, min_cargo_coverage=1.0,
                       activity_group_cuts=experiment["port_selection"]["activity_group_cuts"], features=FEATURES,
                       clipping=False, information_cutoff="protocol same-day-availability scenario; historical availability unverified")
    validation_audit = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                        "status": "diagnostic_complete; joint_task2_review_pending", "frozen": False,
                        "config": used_config, "panel_sha256": audit["panel_sha256"],
                        "script_sha256": sha256(__file__), "preparation_script_sha256": audit["preparation_script_sha256"],
                        "common_keys_sha256": key_hash, "common_validation_ports": len(common_ports),
                        "common_validation_rows": len(evaluation), "models": settings,
                        "origin_counts": origin_counts, "metrics": scores, "recommended_rule": recommended,
                        "active20_minus_coverage_only": {"MAE_tonnes": -mae_improvement,
                                                         "MAE_change_pct": -relative_improvement, "RMSE_tonnes": rmse_change},
                        "recommendation_scope": "Only this fixed linear diagnostic on the common eligible cohort; requires Task 2 review before rule freeze",
                        "test_scored": False, "last_measurement_used": experiment["validation_end"],
                        "runtime_seconds": time.perf_counter() - started,
                        "versions": audit["versions"], "python": audit["python"]}
    write_json(args.results_dir / "eligibility_validation.json", validation_audit)
    experiment["eligibility_validation"] = {
        "status": "diagnostic_complete; joint_task2_review_pending", "recommended_rule": recommended,
        "common_keys_sha256": key_hash, "common_validation_rows": len(evaluation),
        "common_validation_ports": len(common_ports), "test_scored": False, "frozen": False,
        "report": "results/eligibility_validation.md",
        "information_cutoff": "protocol same-day-availability scenario; historical availability unverified",
    }
    experiment["status"] = "task1_outputs_and_validation_diagnostic_prepared; joint_review_and_rule_freeze_pending"
    write_json(args.experiment, experiment)
    rules_path = args.results_dir / "port_selection_rules.json"
    if rules_path.exists():
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        if rules["rule"] != experiment["port_selection"]:
            raise ValueError("Stored candidate rules differ from experiment.json; rerun preparation")
        rules["validation_diagnostic"] = experiment["eligibility_validation"]
        write_json(rules_path, rules)
    view = score_table.copy()
    for column in ["MAE", "RMSE", "WAPE_pct", "macro_port_MAE"]:
        view[column] = view[column].map(lambda x: "NA" if pd.isna(x) else f"{x:.4f}")
    report = f"""# Task 1 eligibility validation sensitivity

Status: diagnostic complete; joint Task 2 review and rule freeze pending. This is a reproducible Task 1 handoff, not a claim that Task 2 owners have reviewed results or completed their production learning table.

## Prespecified comparison

The user reported Dinh and Hieu's agreement to train on 2019-01-01 through 2024-12-31, validate on 2025-01-01 through 2025-12-31 and reserve 2026-01-01 through 2026-10-02 for test. Candidate definitions were recorded before this run: complete training cargo coverage alone, versus the same coverage plus positive cargo on at least 20% of training calendar days. Both retain all observed zeros. Eligibility and the one-third/two-thirds activity bands use training observations only. No source-name filter or full-snapshot activity share determines eligibility.

For a controlled pooled-training comparison, the diagnostic uses the shared protocol's fixed multivariate linear regression with an intercept. Inputs are cargo sum and calls sum from t-6 through t and mean cargo from t-27 through t. The target is one cargo total from t+1 through t+7. Feature scaling is fitted on each candidate's training rows only. Predictions are not clipped; the same setting is used for both candidates. Seasonal naive, equal to cargo_7d, is a reference: its identical predictions on shared rows cannot identify an eligibility winner.

## Common evaluation population and exclusions

All models and both candidates use exactly {len(evaluation):,} validation origins across {len(common_ports)} ports, with complete history and future labels. Common-key SHA-256: `{key_hash}`. Validation origins run from {evaluation.date.min():%Y-%m-%d} through {evaluation.date.max():%Y-%m-%d}; target dates stay inside calendar 2025. Training origins require target_end <= 2024-12-31; validation origins require origin >= 2024-12-31 and target_end <= 2025-12-31. The initial 28-day history and crossing-boundary exclusions are explicit. Past feature history may precede the validation boundary.

{markdown_table(pd.DataFrame(origin_counts), ['eligibility_rule', 'eligible_ports', 'training_rows', 'common_validation_rows', 'validation_rows_excluded_by_common_set'])}

Port rules can change training rows but cannot change these scoring keys. All candidate-rejected ports and training statistics can be reconstructed from `port_selection_audit.csv` and the two thresholds; the complete common key list is `eligibility_validation_keys.csv`. `eligibility_origin_exclusions.csv` records calendar/window exclusions and validation keys outside the common cohort; `eligibility_exclusion_summary.csv` summarizes them. `eligibility_training_exclusions.csv` separately records every complete training key rejected by each candidate's port rule. `eligibility_country_retention.csv` records every country's source, retained and common-evaluation port counts for both candidates. Zero targets remain in scoring, including WAPE's numerator.

{markdown_table(excluded_summary, ['split', 'exclusion_reason', 'rows'])}

## Validation results

{markdown_table(view, ['eligibility_rule', 'model', 'n_rows', 'n_ports', 'MAE', 'RMSE', 'WAPE_pct', 'macro_port_MAE', 'zero_actual_windows', 'negative_predictions'])}

MAE and RMSE are tonnes per seven-day target; WAPE is a percentage computed from sums, with NA for a zero actual-total denominator. Macro-port MAE weights ports equally. Country, training-activity and per-port breakdowns are in `eligibility_validation_breakdown.csv`. Separate prediction files use the protocol's exact ten-column schema; all rows have split=validation. No final test prediction or score is generated.

The lower validation MAE in the fixed linear diagnostic recommends **{recommended}** for joint review. Relative to coverage-only eligibility, the 20% candidate changes MAE by {-mae_improvement:.4f} tonnes ({-relative_improvement:.4f}%) and RMSE by {rmse_change:.4f} tonnes. The MAE difference is very small and RMSE need not favour the same candidate; this is not evidence of a robust or statistically established improvement. Seven-day targets at consecutive origins overlap, so observations are dependent and summed targets are not distinct weekly trade totals.

This comparison is not evidence that the same rule wins for RF/HGB, every feature set or ports outside the common cohort. The common cohort omits lower-training-activity ports excluded by the 20% candidate, so these scores cannot establish forecast quality for those additional ports. Country retention must be considered alongside validation error. The final rule remains unfrozen until Task 2 reviews and reproduces the comparison; dates alone do not imply agreement to this recommendation.

## Limits and handoff

This diagnostic assumes observations through t are available, as in the shared protocol. Historical publication timestamps and revision vintages are unavailable. It is a retrospective same-day-availability scenario, not a verified operational backtest; Task 2 must confirm or explicitly revise that convention. The implementation discards all measurements after 2025-12-31 before constructing any feature or label. Test values do not enter fitting, thresholds, model settings or scoring. Feature and metric boundary checks are exercised by the unit tests.

Joint review should verify common keys, denominators, exclusions, information availability and the recommendation before freezing the selection rules. Task 2's production scripts and full four-baseline comparison remain its owners' deliverables. No messages or approvals from Task 2 owners are fabricated here. Large prediction/key tables stay local and ignored by Git.
"""
    (args.results_dir / "eligibility_validation.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps({"recommended_rule": recommended, "common_validation_ports": len(common_ports),
                      "common_validation_rows": len(evaluation), "metrics": scores,
                      "test_scored": False, "frozen": False}, indent=2))


if __name__ == "__main__":
    main()
