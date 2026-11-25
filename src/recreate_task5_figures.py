"""Recreate the four primary Task 5 figure views from frozen forecasts and metrics."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

from evaluate import align_forecasts, reference_rows, score
from report_task5_han import compare_metrics, digest, primary_metrics, relative_metrics


NAIVE = "seasonal_naive"
OLS = "linear_multivariate"
FOREST = "random_forest"
BOOSTING = "hist_gradient_boosting"
LABEL = {NAIVE: "Seasonal naïve", OLS: "Multivariate linear", FOREST: "Random Forest",
         BOOSTING: "Histogram Gradient Boosting", "linear_univariate": "Univariate linear",
         "polynomial_degree2": "Quadratic regression"}
TEAL, GRAY, NAVY, GOLD = "#007E80", "#8396A8", "#192C3E", "#A66D38"


def save(fig, out, name):
    fig.savefig(out / f"recreated_{name}.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def overall_plot(metrics, out):
    data = metrics.loc[metrics.group_type.eq("overall")].sort_values("MAE")
    fig, ax = plt.subplots(figsize=(10, 4.3), layout="constrained")
    bars = ax.barh(data.model.map(LABEL), data.MAE / 1000,
                   color=[TEAL] + [GRAY] * (len(data) - 1))
    ax.bar_label(bars, fmt="%.2f", padding=5)
    ax.invert_yaxis()
    ax.set(xlim=(0, data.MAE.max() / 1000 + 9), xlabel="MAE (thousand tonnes per seven-day forecast)")
    ax.set_title("Multivariate regression has the lowest test MAE", loc="left", fontweight="bold")
    save(fig, out, "overall_mae")


def activity_plot(metrics, out):
    groups = ["low", "medium", "high"]
    data = relative_metrics(metrics.loc[metrics.group_type.eq("activity")])
    fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
    positions = np.arange(len(groups))
    for i, (model, color) in enumerate([(OLS, TEAL), (FOREST, GRAY), (BOOSTING, GOLD)]):
        rows = data.loc[data.model.eq(model)].set_index("group").loc[groups]
        bars = ax.barh(positions + (i - 1) * .23, -rows.MAE_change_vs_naive_pct, height=.20,
                       label=LABEL[model], color=color)
        ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=9)
    counts = data.loc[data.model.eq(NAIVE)].set_index("group").n_ports
    ax.set_yticks(positions, [f"{g.title()} activity ({counts[g]} ports)" for g in groups])
    ax.set_xlim(0, max(30, -data.MAE_change_vs_naive_pct.min() + 5))
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(PercentFormatter(100))
    ax.set_xlabel("Test MAE reduction relative to seasonal naïve within each activity group")
    ax.set_title("The lowest MAE varies by port activity", loc="left", fontweight="bold")
    fig.legend(loc="outside upper left", ncols=3, frameon=False, fontsize=9)
    save(fig, out, "activity_mae")


def port_plot(primary, ols, out):
    means = ols.groupby("port_id", as_index=False).y_true.mean().sort_values(["y_true", "port_id"])
    median_port = means.iloc[(len(means) - 1) // 2].port_id
    choices = [("port434", "Hải Phòng (port434)"), (median_port, f"Lower middle port by mean cargo ({median_port})")]
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.1), sharex=True, layout="constrained")
    for ax, (pid, title) in zip(axes, choices):
        observed = ols.loc[ols.port_id.eq(pid)].sort_values("origin_date")
        ax.plot(pd.to_datetime(observed.origin_date), observed.y_true / 1000, color=NAVY, label="Observed")
        for model, color in [(OLS, TEAL), (NAIVE, GRAY)]:
            predictions = primary.loc[primary.port_id.eq(pid) & primary.model.eq(model)].sort_values("origin_date")
            ax.plot(pd.to_datetime(predictions.origin_date), predictions.y_pred / 1000,
                    color=color, label=LABEL[model])
        ax.set(title=title, ylabel="Thousand tonnes", ylim=(0, None))
        ax.grid(axis="y", alpha=.23)
    axes[0].legend(ncol=3, loc="lower center", frameon=False)
    axes[-1].set_xlabel("Forecast origin (each point covers the following seven days)")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.suptitle("Observed and predicted cargo at two ports", fontweight="bold")
    save(fig, out, "observed_predicted")
    return median_port


def error_plot(ols, out):
    misses = ols.assign(absolute_error=(ols.y_pred - ols.y_true).abs())
    cases = misses.sort_values(["absolute_error", "port_id", "origin_date"], ascending=[False, True, True])
    cases = cases.drop_duplicates("port_id").head(5)
    fig, ax = plt.subplots(figsize=(10.4, 4.5), layout="constrained")
    positions = np.arange(len(cases))
    actual, predicted = cases.y_true / 1e6, cases.y_pred / 1e6
    ax.hlines(positions, np.minimum(actual, predicted), np.maximum(actual, predicted), color=GRAY, lw=3)
    ax.scatter(actual, positions, color=NAVY, label="Observed", zorder=3)
    ax.scatter(predicted, positions, color=TEAL, marker="D", label=LABEL[OLS], zorder=3)
    for i, error, under in zip(positions, cases.absolute_error / 1e6, predicted.lt(actual)):
        ax.text(max(actual.max(), predicted.max()) + .7, i, f'{error:.2f}M t {"under" if under else "over"}', va="center")
    ax.set_yticks(positions, [f"{r.port_id} ({r.country_iso3})\n{r.origin_date}" for r in cases.itertuples()])
    ax.set(xlim=(0, max(actual.max(), predicted.max()) + 5.2), xlabel="Estimated seven-day cargo (million tonnes)")
    ax.invert_yaxis()
    fig.legend(loc="outside upper left", frameon=False, ncols=2)
    ax.set_title("Large forecast misses in multivariate regression", loc="left", fontweight="bold")
    save(fig, out, "large_errors")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, default=Path("results/task5_test/test_predictions.csv"))
    parser.add_argument("--reference", type=Path, default=Path("results/task5_test/test_reference.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/task5_test/recreated_figures"))
    args = parser.parse_args()
    record = json.loads(Path("results/task5_test_run.json").read_text(encoding="utf-8"))
    freeze_path = Path("results/task5_freeze.json")
    metrics_path = Path("results/metrics.csv")
    if digest(metrics_path) != record["output_sha256"]["metrics.csv"] or digest(freeze_path) != record["freeze_sha256"]:
        raise ValueError("The frozen Task 5 metrics or comparison scope have changed")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    config = json.loads(Path("experiment.json").read_text(encoding="utf-8"))
    expected = pd.read_csv(metrics_path, dtype={"group": str})
    metrics = primary_metrics(expected, pd.read_csv("results/task5_test_summary.csv"), freeze)
    reference = reference_rows(pd.read_csv(args.reference), config, "test")
    aligned, _ = align_forecasts(pd.read_csv(args.predictions), reference, "test")
    checked, _ = score(aligned, "all_eligible")
    compare_metrics(checked, expected)
    variants = metrics.loc[metrics.group_type.eq("overall"), ["model", "feature_set"]]
    primary = aligned.merge(variants, on=["model", "feature_set"], validate="many_to_one")
    ols = primary.loc[primary.model.eq(OLS)]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 11})
    overall_plot(metrics, args.out_dir)
    activity_plot(metrics, args.out_dir)
    median_port = port_plot(primary, ols, args.out_dir)
    error_plot(ols, args.out_dir)
    print(f"Verified {len(checked):,} metric rows and recreated four figure views in {args.out_dir}. Median example: {median_port}.")


if __name__ == "__main__":
    main()
