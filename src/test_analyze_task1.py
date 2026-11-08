"""Independent calendar examples, leakage guards and scoring checks for Task 1."""
import unittest
import numpy as np
import pandas as pd

from analyze_task1 import build_windows, training_ports, zero_runs, fit_ols, metrics, block_interval, positive_observation_spans


def example():
    dates = pd.date_range("2024-11-01", "2025-02-15")
    parts = []
    for pid, value in [("p1", 1.), ("p2", 10.)]:
        parts.append(pd.DataFrame({"date": dates, "port_id": pid, "country_iso3": "VNM",
            "cargo_tonnes": value, "portcalls": 2.}))
    return pd.concat(parts, ignore_index=True)


CONFIG = {"train_start": "2024-11-01", "train_end": "2024-12-31", "validation_end": "2025-01-31",
          "port_selection": {"activity_group_cuts": [1/3, 2/3], "candidate_active_share": .2}}


class Task1Tests(unittest.TestCase):
    def test_deleting_zeros_changes_calendar_horizon(self):
        p = example().iloc[:20].copy()
        p["cargo_tonnes"] = np.arange(20) % 2
        self.assertTrue(positive_observation_spans(p).days.eq(14).all())

    def test_hand_worked_windows_and_boundaries(self):
        f = build_windows(example(), CONFIG)
        row = f.loc[f.port_id.eq("p1") & f.date.eq("2024-12-31")].iloc[0]
        self.assertEqual((row.cargo_7d, row.calls_7d, row.cargo_mean_28d, row.y_true), (7, 14, 1, 7))
        self.assertEqual(row.target_start, pd.Timestamp("2025-01-01"))
        self.assertEqual(row.target_end, pd.Timestamp("2025-01-07"))
        self.assertEqual(row.split, "validation")
        self.assertEqual(f.loc[f.split.eq("train"), "date"].max(), pd.Timestamp("2024-12-24"))
        self.assertEqual(f.loc[f.split.eq("validation"), "date"].max(), pd.Timestamp("2025-01-24"))
        self.assertTrue(f.loc[f.date.between("2024-12-25", "2024-12-30"), "split"].eq("excluded").all())
        self.assertEqual(f.loc[f.port_id.eq("p2") & f.date.eq("2024-12-31"), "y_true"].iloc[0], 70)

    def test_future_perturbation_cannot_change_features_or_selection(self):
        p = example(); base = build_windows(p, CONFIG, True)
        p.loc[p.date.gt("2025-01-10"), ["cargo_tonnes", "portcalls"]] = 9e9
        changed = build_windows(p, CONFIG, True)
        cols = ["cargo_7d", "calls_7d", "cargo_mean_28d", "history_cargo"]
        pd.testing.assert_frame_equal(base.loc[base.date.le("2025-01-10"), cols], changed.loc[changed.date.le("2025-01-10"), cols])
        pd.testing.assert_frame_equal(training_ports(example(), CONFIG), training_ports(p, CONFIG))
        # Test values are discarded entirely, even from future labels.
        p = example(); p.loc[p.date.gt("2025-01-31"), ["cargo_tonnes", "portcalls"]] = np.nan
        pd.testing.assert_frame_equal(base, build_windows(p, CONFIG, True))

    def test_causal_replacement_and_original_target(self):
        p = example(); p.loc[p.port_id.eq("p1"), "cargo_tonnes"] = 0.
        p.loc[p.port_id.eq("p1") & p.date.eq("2024-11-10"), "cargo_tonnes"] = 8.
        f = build_windows(p, CONFIG, True).set_index(["port_id", "date"])
        self.assertEqual(f.loc[("p1", "2024-11-09"), "history_cargo"], 0)
        self.assertEqual(f.loc[("p1", "2024-11-11"), "history_cargo"], 8)
        self.assertEqual(f.loc[("p1", "2024-12-09"), "history_cargo"], 0)
        a = build_windows(p, CONFIG)
        np.testing.assert_allclose(f.y_true.to_numpy(), a.y_true.to_numpy(), equal_nan=True)

    def test_integer_source_allows_fractional_past_mean(self):
        p = example(); p["cargo_tonnes"] = 0
        p.loc[p.port_id.eq("p1") & p.date.eq("2024-11-01"), "cargo_tonnes"] = 1
        p.loc[p.port_id.eq("p1") & p.date.eq("2024-11-02"), "cargo_tonnes"] = 2
        f = build_windows(p, CONFIG, True)
        self.assertEqual(f.loc[f.port_id.eq("p1") & f.date.eq("2024-11-03"), "history_cargo"].iloc[0], 1.5)

    def test_missing_is_never_zero_and_breaks_runs(self):
        p = example().loc[lambda x: x.port_id.eq("p1")].copy()
        p["cargo_tonnes"] = 0.
        p.loc[p.date.eq("2024-11-04"), "cargo_tonnes"] = np.nan
        runs = zero_runs(p)
        self.assertEqual(runs.days.tolist(), [3, len(p)-4])
        self.assertTrue(runs.left_censored.iloc[0]); self.assertTrue(runs.right_censored.iloc[1])
        w = build_windows(p, CONFIG, True)
        self.assertTrue(pd.isna(w.loc[w.date.eq("2024-11-04"), "history_cargo"].iloc[0]))
        self.assertFalse(training_ports(p, CONFIG).selected.iloc[0])

    def test_training_denominators_and_group_edges(self):
        cfg = dict(CONFIG, train_start="2024-11-01", train_end="2024-11-30")
        p = example(); p["cargo_tonnes"] = 0.
        p.loc[p.port_id.eq("p1") & p.date.between("2024-11-01", "2024-11-06"), "cargo_tonnes"] = 1
        p.loc[p.port_id.eq("p2") & p.date.between("2024-11-01", "2024-11-20"), "cargo_tonnes"] = 1
        s = training_ports(p, cfg).set_index("port_id")
        self.assertEqual(s.loc["p1", "train_calendar_days"], 30)
        self.assertTrue(s.loc["p1", "candidate_active20"])
        self.assertEqual(s.loc["p2", "activity_group"], "high")

    def test_metrics_include_zero_errors_and_undefined_wape(self):
        f = pd.DataFrame({"port_id": ["a", "b"], "y_true": [0., 10.], "y_pred": [4., 6.]})
        m = metrics(f)
        self.assertEqual((m["MAE"], m["RMSE"], m["WAPE_pct"]), (4, 4, 80))
        self.assertTrue(np.isnan(metrics(f.iloc[:1])["WAPE_pct"]))
        self.assertEqual(metrics(f.iloc[:1])["MAE"], 4)

    def test_ols_train_fit_only_and_block_pairing(self):
        rng = np.random.default_rng(9)
        f = pd.DataFrame(rng.normal(size=(100, 3)), columns=["cargo_7d", "calls_7d", "cargo_mean_28d"])
        f["y_true"] = 3+2*f.cargo_7d-f.calls_7d+.5*f.cargo_mean_28d
        predicted, _ = fit_ols(f.iloc[:80], f.iloc[80:])
        np.testing.assert_allclose(predicted, f.y_true.iloc[80:], atol=1e-12)
        self.assertEqual(block_interval(np.full(100, 4.), 28, 50), (4., 4., 4.))

    def test_calendar_gaps_and_duplicates_rejected(self):
        p = example()
        with self.assertRaises(ValueError):
            build_windows(p.drop(index=10), CONFIG)
        with self.assertRaises(ValueError):
            build_windows(pd.concat([p, p.iloc[:1]]), CONFIG)


if __name__ == "__main__":
    unittest.main()
