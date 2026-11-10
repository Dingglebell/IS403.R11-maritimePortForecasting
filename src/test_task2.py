"""Task 2 checks with independent calendar and regression examples."""

import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from features import build_learning_table, FEATURES, sha256
from baselines import predict_baselines, fit_regression, score_predictions

CONFIG = {
    "horizon_days": 7, "history_days": [7, 28], "train_start": "2024-10-01",
    "train_end": "2024-12-31", "validation_end": "2025-02-28", "test_end": "2025-03-31",
    "port_selection": {"handoff_rule": "complete_training_coverage", "activity_group_cuts": [1/3, 2/3],
                       "candidate_active_share": .2}, "pool_ports": True, "refit_before_test": False,
    "clip_negative_predictions": None,
}


def panel():
    dates = pd.date_range(CONFIG["train_start"], CONFIG["test_end"])
    parts = []
    for pid, multiplier in [("A", 1), ("B", 10)]:
        cargo = multiplier * (np.arange(len(dates)) % 13).astype(float)
        parts.append(pd.DataFrame({"port_id": pid, "date": dates, "country_iso3": "VNM",
            "import_tonnes": cargo, "export_tonnes": 0., "cargo_tonnes": cargo, "portcalls": 2.}))
    return pd.concat(parts, ignore_index=True)


class Task2Checks(unittest.TestCase):
    def test_calendar_values_are_hand_summed_and_ports_isolated(self):
        p = panel()
        table, _, _ = build_learning_table(p, CONFIG)
        t = pd.Timestamp("2024-12-31")
        for pid in ["A", "B"]:
            g = p.loc[p.port_id.eq(pid)].set_index("date")
            row = table.loc[table.port_id.eq(pid) & table.origin_date.eq(t)].iloc[0]
            self.assertEqual(row.cargo_7d, g.loc[t-pd.Timedelta(days=6):t, "cargo_tonnes"].sum())
            self.assertEqual(row.calls_7d, 14)
            self.assertAlmostEqual(row.cargo_mean_28d, g.loc[t-pd.Timedelta(days=27):t, "cargo_tonnes"].mean())
            self.assertEqual(row.target_7d, g.loc["2025-01-01":"2025-01-07", "cargo_tonnes"].sum())
            self.assertEqual(row.split, "validation")
        self.assertEqual(table.loc[table.split.eq("train"), "origin_date"].max(), pd.Timestamp("2024-12-24"))
        self.assertEqual(table.loc[table.split.eq("validation"), "origin_date"].max(), pd.Timestamp("2025-02-21"))

    def test_test_values_cannot_change_any_outputs(self):
        original = panel()
        changed = original.copy()
        changed.loc[changed.date.gt(CONFIG["validation_end"]), ["cargo_tonnes", "import_tonnes", "portcalls"]] = -999
        for a, b in zip(build_learning_table(original, CONFIG), build_learning_table(changed, CONFIG)):
            pd.testing.assert_frame_equal(a, b)

    def test_validation_changes_cannot_change_training_or_selection(self):
        original = panel()
        changed = original.copy()
        changed.loc[changed.date.gt(CONFIG["train_end"]), ["cargo_tonnes", "import_tonnes"]] = 9e8
        a, ports_a, _ = build_learning_table(original, CONFIG)
        b, ports_b, _ = build_learning_table(changed, CONFIG)
        pd.testing.assert_frame_equal(ports_a, ports_b)
        pd.testing.assert_frame_equal(a.loc[a.split.eq("train")], b.loc[b.split.eq("train")])

    def test_missing_history_excludes_rows_instead_of_becoming_zero(self):
        p = panel()
        missing = p.port_id.eq("A") & p.date.eq("2025-01-10")
        p.loc[missing, ["cargo_tonnes", "import_tonnes"]] = np.nan
        table, ports, excluded = build_learning_table(p, CONFIG)
        self.assertTrue(ports.selected.all())  # missingness occurs after training
        self.assertFalse((table.port_id.eq("A") & table.origin_date.eq("2025-01-10")).any())
        self.assertTrue(excluded.exclusion_reason.eq("incomplete_history").any())
        zero_panel = panel()
        zero_panel.loc[missing, ["cargo_tonnes", "import_tonnes"]] = 0
        zero_table, _, _ = build_learning_table(zero_panel, CONFIG)
        self.assertTrue((zero_table.port_id.eq("A") & zero_table.origin_date.eq("2025-01-10")).any())

    def test_incomplete_training_port_is_excluded_without_future_selection(self):
        p = panel()
        p.loc[p.port_id.eq("B") & p.date.eq("2024-10-15"), "portcalls"] = np.nan
        table, ports, excluded = build_learning_table(p, CONFIG)
        self.assertEqual(set(table.port_id), {"A"})
        self.assertFalse(ports.set_index("port_id").loc["B", "selected"])
        self.assertTrue(excluded.exclusion_reason.eq("incomplete_training_port_coverage").any())

    def test_gaps_duplicate_keys_and_wrong_cargo_are_rejected(self):
        p = panel()
        bad = p.copy(); bad.loc[0, "cargo_tonnes"] = 9
        for f in [p.drop(index=10), pd.concat([p, p.iloc[:1]]), bad]:
            with self.subTest(), self.assertRaises(ValueError):
                build_learning_table(f, CONFIG)

    def test_all_models_use_identical_rows_and_naive_is_last_week(self):
        table, _, _ = build_learning_table(panel(), CONFIG)
        predicted, _ = predict_baselines(table, CONFIG)
        expected = table.loc[table.split.eq("validation")].sort_values(["port_id", "origin_date"])
        self.assertEqual(predicted.model.nunique(), 4)
        for _, f in predicted.groupby("model"):
            np.testing.assert_array_equal(f.origin_date, expected.origin_date)
            np.testing.assert_array_equal(f.port_id, expected.port_id)
            np.testing.assert_array_equal(f.y_true, expected.target_7d)
        np.testing.assert_array_equal(predicted.loc[predicted.model.eq("seasonal_naive"), "y_pred"], expected.cargo_7d)

    def test_regression_recovers_known_linear_and_quadratic_functions(self):
        x = np.linspace(1, 200, 100)
        f = pd.DataFrame({"cargo_7d": x, "target_7d": 3 + 2*x})
        pred, _ = fit_regression(f.iloc[:80], f.iloc[80:], ["cargo_7d"])
        np.testing.assert_allclose(pred, f.target_7d.iloc[80:], rtol=1e-12)
        f["target_7d"] = 5 + 3*x + .4*x*x
        pred, _ = fit_regression(f.iloc[:80], f.iloc[80:], ["cargo_7d"], quadratic=True)
        np.testing.assert_allclose(pred, f.target_7d.iloc[80:], rtol=1e-12)

    def test_validation_targets_do_not_change_fitted_models_or_predictions(self):
        table, _, _ = build_learning_table(panel(), CONFIG)
        a, fits_a = predict_baselines(table, CONFIG)
        changed = table.copy()
        changed.loc[changed.split.eq("validation"), "target_7d"] = 9e8
        b, fits_b = predict_baselines(changed, CONFIG)
        np.testing.assert_array_equal(a.y_pred, b.y_pred)
        self.assertEqual(fits_a, fits_b)

    def test_multivariate_recovers_known_function_and_uses_training_scaling(self):
        rng = np.random.default_rng(42)
        f = pd.DataFrame(rng.uniform(1, 100, size=(100, 3)), columns=FEATURES)
        f["target_7d"] = 11 + f[FEATURES].to_numpy() @ np.array([2., 3., 4.])
        pred, fit = fit_regression(f.iloc[:80], f.iloc[80:], FEATURES)
        np.testing.assert_allclose(pred, f.target_7d.iloc[80:], rtol=1e-12)
        np.testing.assert_allclose(fit["training_mean"], f.iloc[:80][FEATURES].mean())
        self.assertEqual(fit["rank"], 4)

    def test_baseline_rejects_origins_without_required_history(self):
        table, _, _ = build_learning_table(panel(), CONFIG)
        table.loc[0, "origin_date"] = pd.Timestamp(CONFIG["train_start"])
        table.loc[0, "target_start"] = table.loc[0, "origin_date"] + pd.Timedelta(days=1)
        table.loc[0, "target_end"] = table.loc[0, "origin_date"] + pd.Timedelta(days=7)
        with self.assertRaisesRegex(ValueError, "28-day"):
            predict_baselines(table, CONFIG)

    def test_standalone_cli_exports_aligned_variants_and_reproducible_record(self):
        table, _, _ = build_learning_table(panel(), CONFIG)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            table.to_csv(root / "table.csv", index=False)
            (root / "config.json").write_text(json.dumps(CONFIG), encoding="utf-8")
            completed = subprocess.run([sys.executable, str(Path(__file__).with_name("baselines.py")),
                "--table", str(root / "table.csv"), "--experiment", str(root / "config.json"),
                "--results-dir", str(root)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            raw = pd.read_csv(root / "baseline_none_predictions.csv")
            clipped = pd.read_csv(root / "baseline_nonnegative_predictions.csv")
            pd.testing.assert_frame_equal(raw.drop(columns=["y_pred", "clipping"]),
                                          clipped.drop(columns=["y_pred", "clipping"]))
            np.testing.assert_allclose(clipped.y_pred, np.maximum(raw.y_pred, 0))
            scores = pd.read_csv(root / "baseline_metrics.csv")
            for rule, forecasts in [("none", raw), ("nonnegative", clipped)]:
                for model, f in forecasts.groupby("model"):
                    actual = scores.loc[scores.model.eq(model) & scores.clipping.eq(rule)].iloc[0]
                    errors = (f.y_true - f.y_pred).to_numpy()
                    self.assertAlmostEqual(actual.MAE, np.mean(np.abs(errors)))
                    self.assertAlmostEqual(actual.RMSE, np.sqrt(np.mean(errors ** 2)))
                    self.assertAlmostEqual(actual.WAPE_pct, 100 * np.abs(errors).sum() / f.y_true.sum())
            record = json.loads((root / "baseline_run.json").read_text(encoding="utf-8"))
            self.assertFalse(record["test_scored"])
            self.assertEqual(record["learning_table_sha256"], sha256(root / "table.csv"))
            for name, digest in record["output_sha256"].items():
                self.assertEqual(digest, sha256(root / name))

    def test_metrics_zero_denominator_and_test_split_guard(self):
        f = pd.DataFrame({"model": "example", "feature_set": "cargo_only", "port_id": ["A", "B"],
                          "y_true": [0., 10.], "y_pred": [4., 6.]})
        m = score_predictions(f).iloc[0]
        self.assertEqual((m.MAE, m.RMSE, m.WAPE_pct), (4, 4, 80))
        self.assertTrue(pd.isna(score_predictions(f.iloc[:1]).iloc[0].WAPE_pct))
        table, _, _ = build_learning_table(panel(), CONFIG)
        table.loc[table.split.eq("validation"), "split"] = "test"
        with self.assertRaisesRegex(ValueError, "test is reserved"):
            predict_baselines(table, CONFIG)


if __name__ == "__main__":
    unittest.main()
