"""Han's descriptive Task 5 handoff from Dinh's frozen evaluation; no fitting/tuning."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from evaluate import align_forecasts, reference_rows, score

LABELS = {
    "seasonal_naive": "Seasonal naive", "linear_univariate": "Univariate LR",
    "linear_multivariate": "Multivariate LR", "polynomial_degree2": "Degree-2 LR",
    "random_forest": "Random Forest", "hist_gradient_boosting": "HGB",
}
ORDER = list(LABELS)
KEY = ["model", "feature_set", "split", "scope", "group_type", "group"]
VALUES = ["n_rows", "n_ports", "zero_actual_rows", "MAE", "RMSE", "WAPE_pct", "macro_port_MAE", "mean_bias"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def csv(frame, path):
    frame.to_csv(path, index=False, lineterminator="\n")


def table(frame):
    f = frame.copy()
    for col in f:
        if pd.api.types.is_float_dtype(f[col]):
            f[col] = f[col].map(lambda x: "NA" if pd.isna(x) else f"{x:,.2f}")
    return "| " + " | ".join(f.columns) + " |\n| " + " | ".join(["---"]*len(f.columns)) + " |\n" + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in f.itertuples(index=False, name=None))


def compare_metrics(actual, expected):
    """Compare every group/key; allow only tiny floating-point export differences."""
    a = actual.assign(group=actual.group.astype(str)).sort_values(KEY).reset_index(drop=True)
    e = expected.assign(group=expected.group.astype(str)).sort_values(KEY).reset_index(drop=True)
    pd.testing.assert_frame_equal(a[KEY], e[KEY], check_dtype=False)
    np.testing.assert_allclose(a[VALUES], e[VALUES], rtol=1e-8, atol=1e-6, equal_nan=True)


def primary_metrics(metrics, summary, freeze):
    variants = summary.loc[summary.primary_comparison, ["model", "feature_set"]]
    if variants.duplicated().any() or set(variants.model+"/"+variants.feature_set) != set(freeze["primary_comparison"]):
        raise ValueError("Primary cohort differs from pre-test freeze")
    m = metrics.merge(variants, on=["model", "feature_set"], validate="many_to_one")
    if not m.split.eq("test").all() or not m.scope.eq("all_eligible").all() or m.duplicated(KEY).any():
        raise ValueError("Expected unique test metrics for all eligible ports")
    return m


def relative_metrics(frame):
    naive = frame.loc[frame.model.eq("seasonal_naive"), ["group_type", "group", "MAE"]].rename(columns={"MAE": "naive_MAE"})
    out = frame.merge(naive, on=["group_type", "group"], validate="many_to_one")
    out["MAE_change_vs_naive_pct"] = np.where(out.naive_MAE.gt(0), 100*(out.MAE/out.naive_MAE-1), np.nan)
    out["beats_naive_MAE"] = out.MAE.lt(out.naive_MAE)
    return out


def make_tables(m, ports, out):
    expanded = relative_metrics(m)
    for name, kinds in [("country_activity", ["country", "activity"]), ("zero_positive", ["actual_volume"]),
                        ("weekly_phases", ["weekly_phase"]), ("overall", ["overall"])]:
        csv(expanded.loc[expanded.group_type.isin(kinds)], out / f"{name}.csv")
    p = expanded.loc[expanded.group_type.eq("port")].rename(columns={"group": "port_id"}).merge(
        ports[["port_id", "country_iso3", "activity_group"]], on="port_id", validate="many_to_one")
    csv(p, out / "per_port.csv")
    # Equal-weight summaries of each port, with tie-aware wins and zero-denominator counts.
    best = p.groupby("port_id").MAE.transform("min")
    p["tied_best"] = np.isclose(p.MAE, best, rtol=1e-10, atol=1e-8)
    summaries = []
    for model, g in p.groupby("model"):
        summaries.append({"model": model, "ports": len(g), "ports_beating_naive": int(g.beats_naive_MAE.sum()),
            "ports_tied_best": int(g.tied_best.sum()), "median_port_MAE": g.MAE.median(),
            "p90_port_MAE": g.MAE.quantile(.9), "macro_port_MAE": g.MAE.mean(),
            "undefined_port_WAPE": int(g.WAPE_pct.isna().sum())})
    csv(pd.DataFrame(summaries), out / "port_summary.csv")
    # Total absolute-error contributions; these are overlapping-window error burdens, not cargo totals.
    c = expanded.loc[expanded.group_type.eq("country")].copy()
    c["absolute_error_sum"] = c.MAE*c.n_rows
    c["absolute_error_share_pct"] = 100*c.absolute_error_sum/c.groupby("model").absolute_error_sum.transform("sum")
    csv(c, out / "country_error_contributions.csv")
    sections = []
    for kind in ["overall", "country", "activity", "actual_volume", "weekly_phase"]:
        f = expanded.loc[expanded.group_type.eq(kind), ["model", "group", "n_rows", "n_ports", "MAE", "RMSE", "WAPE_pct", "mean_bias", "MAE_change_vs_naive_pct"]]
        sections.append(f"## {kind}\n\n{table(f)}")
    (out / "tables.md").write_text("# Task 5 primary comparison (generated)\n\nSource: Dinh's frozen test metrics. All tonnes are per seven-day forecast window. NA WAPE has zero actual denominator. Negative MAE change improves on naive.\n\n"+"\n\n".join(sections)+"\n", encoding="utf-8")
    return expanded, p


def figures(m, out):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    overall = m.loc[m.group_type.eq("overall")].set_index("model").loc[ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for ax, metric in zip(axes, ["MAE", "RMSE"]):
        ax.barh([LABELS[k] for k in ORDER], overall[metric]/1000, color="#287A91")
        ax.invert_yaxis(); ax.set_xlabel(f"{metric}, thousand tonnes / 7-day target")
    fig.suptitle("Frozen test comparison — 56,490 identical origins per variant")
    fig.savefig(out / "overall.png", dpi=160); plt.close(fig)
    country = m.loc[m.group_type.eq("country")].pivot(index="group", columns="model", values="MAE_change_vs_naive_pct")[ORDER[1:]]
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    limit = max(40, np.nanmax(np.abs(country.to_numpy())))
    im = ax.imshow(country, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(len(country.columns)), [LABELS[k] for k in country.columns], rotation=20, ha="right")
    ax.set_yticks(range(len(country)), country.index)
    for i in range(len(country)):
        for j in range(len(country.columns)):
            ax.text(j, i, f"{country.iloc[i,j]:+.1f}%", ha="center", va="center", fontsize=9,
                    color="white" if abs(country.iloc[i,j]) > .55*limit else "black")
    fig.colorbar(im, ax=ax, label="MAE change vs naive (%); negative is better")
    ax.set_title("Country differences — fixed primary models, not country-specific selection")
    fig.savefig(out / "country_comparison.png", dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), constrained_layout=True)
    for ax, group in zip(axes, ["low", "medium", "high"]):
        g = m.loc[m.group_type.eq("activity") & m.group.eq(group)].set_index("model").loc[ORDER]
        ax.bar(range(6), g.MAE/1000, color="#287A91")
        ax.set_xticks(range(6), [LABELS[k] for k in ORDER], rotation=55, ha="right", fontsize=8)
        ax.set_title(f"{group.title()} activity: {int(g.n_ports.iloc[0])} ports")
        ax.set_ylabel("MAE, thousand tonnes / target")
    fig.suptitle("Activity bands fixed from training; panels have different scales")
    fig.savefig(out / "activity_comparison.png", dpi=160); plt.close(fig)


def forecast_figures(predictions, reference, m, config, out):
    aligned, coverage = align_forecasts(predictions, reference_rows(reference, config, "test"), "test")
    recalculated, _ = score(aligned, "all_eligible")
    compare_metrics(recalculated, m)
    primary = primary_metrics(m, pd.read_csv("results/task5_test_summary.csv"), json.loads(Path("results/task5_freeze.json").read_text()))
    g = primary.loc[primary.group_type.eq("port") & primary.model.eq("linear_multivariate")]
    # Retrospective diagnostic cases, never a new modelling/evaluation population.
    worst_ids = g.sort_values(["MAE", "group"], ascending=[False, True]).group.head(3).tolist()
    display_models = ["seasonal_naive", "linear_multivariate", "random_forest", "hist_gradient_boosting"]
    rows = aligned.loc[aligned.port_id.isin(worst_ids) & aligned.model.isin(display_models)
                       & (aligned.feature_set.eq("all_three") | aligned.model.eq("seasonal_naive")) & aligned.weekly_phase.eq(0)].copy()
    rows["origin_date"] = pd.to_datetime(rows.origin_date)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)
    for ax, pid in zip(axes, worst_ids):
        port = rows.loc[rows.port_id.eq(pid)]
        truth = port.loc[port.model.eq("linear_multivariate")].sort_values("origin_date")
        ax.plot(truth.origin_date, truth.y_true/1000, label="Published actual", color="black", lw=2)
        for model in display_models:
            a = port.loc[port.model.eq(model)].sort_values("origin_date")
            ax.plot(a.origin_date, a.y_pred/1000, label=LABELS[model], alpha=.85, lw=1.1)
        ax.set_title(f"{pid} — {truth.country_iso3.iloc[0]}, {truth.activity_group.iloc[0]} activity")
        ax.set_ylabel("Thousand tonnes / 7 days")
    axes[-1].set_xlabel("Forecast origin date (each target covers the following seven days)")
    axes[0].legend(ncol=3, fontsize=8)
    fig.suptitle("Three largest port MAEs for multivariate LR; every seventh origin (phase 0)")
    fig.savefig(out / "observed_predicted_cases.png", dpi=160); plt.close(fig)
    csv(rows[["model", "feature_set", "port_id", "country_iso3", "origin_date", "target_start", "target_end", "y_true", "y_pred"]], out / "case_windows.csv")
    six = aligned.merge(primary.loc[primary.group_type.eq("overall"), ["model", "feature_set"]], on=["model", "feature_set"], validate="many_to_one")
    six["signed_error"] = six.y_pred-six.y_true
    six["absolute_error"] = six.signed_error.abs()
    cases = pd.concat([f.nlargest(3, "absolute_error") for _, f in six.groupby(["model", "feature_set"])])
    csv(cases.reset_index(drop=True), out / "largest_errors.csv")
    return {"rows": len(predictions), "variants": len(coverage), "metric_rows_verified": len(recalculated),
            "case_ports": worst_ids, "row_level_status": "aligned_and_all_metrics_reproduced"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results/task5_han"))
    args = parser.parse_args()
    record = json.loads(Path("results/task5_test_run.json").read_text())
    freeze = json.loads(Path("results/task5_freeze.json").read_text())
    if digest("results/metrics.csv") != record["output_sha256"]["metrics.csv"]:
        raise ValueError("Leader's metrics changed; review provenance before reporting")
    if digest("results/task5_freeze.json") != record["freeze_sha256"]:
        raise ValueError("Freeze record changed")
    for name, path in [("experiment", "experiment.json"), ("ports", "results/task2_ports.csv")]:
        if digest(path) != freeze["sha256"][name]:
            raise ValueError(f"Frozen {name} changed")
    config = json.loads(Path("experiment.json").read_text())
    m = pd.read_csv("results/metrics.csv", dtype={"group": str})
    summary = pd.read_csv("results/task5_test_summary.csv")
    primary = primary_metrics(m, summary, freeze)
    compare_metrics(m.loc[m.group_type.eq("overall")], summary)
    ports = pd.read_csv("results/task2_ports.csv")
    out = args.out_dir; out.mkdir(parents=True, exist_ok=True)
    expanded, _ = make_tables(primary, ports, out)
    figures(expanded, out)
    proof = forecast_figures(pd.read_csv(args.predictions), pd.read_csv(args.reference), m, config, out)
    proof.update(metrics_sha256=digest("results/metrics.csv"), predictions_sha256=digest(args.predictions),
        reference_sha256=digest(args.reference),
        original_reference_bytes_match=digest(args.reference)==record["output_sha256"]["test_reference.csv"],
        original_prediction_sha256=record["output_sha256"]["test_predictions.csv"],
        original_prediction_bytes_match=digest(args.predictions)==record["output_sha256"]["test_predictions.csv"],
        freeze_sha256=digest("results/task5_freeze.json"), script_sha256=digest(__file__),
        attribution="Han's descriptive analysis of Dinh's frozen Task 5 results; no fit/tuning in this script",
        tolerance="metric comparison rtol=1e-8, atol=1e-6; all keys exact",
        packages={"numpy": np.__version__, "pandas": pd.__version__, "matplotlib": matplotlib.__version__})
    (out / "verification.json").write_text(json.dumps(proof, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
