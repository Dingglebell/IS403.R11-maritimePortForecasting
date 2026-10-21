"""Hand-worked windows, chronological boundaries and metrics for Task 1 review."""

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from validate_port_rules import FEATURES, candidate_lists, fit_linear, metrics, validation_table
from prepare_data import sha256


ROOT = Path(__file__).resolve().parents[1]


class ValidationChecks(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range("2020-01-01", "2020-04-20")
        self.panel = pd.concat([
            pd.DataFrame({"date": dates, "port_id": port, "country_iso3": "VNM",
                          "cargo_tonnes": np.arange(1, len(dates) + 1) * multiplier,
                          "portcalls": np.arange(1, len(dates) + 1) % 3})
            for port, multiplier in [("A", 1), ("B", 100)]
        ], ignore_index=True)
        self.panel[["cargo_tonnes", "portcalls"]] = self.panel[["cargo_tonnes", "portcalls"]].astype(float)
        self.config = {
            "train_start": "2020-01-01", "train_end": "2020-02-29",
            "validation_end": "2020-03-31", "test_end": "2020-04-20",
            "time_split_agreement": {"status": "agreed", "agreed_by": ["Dinh", "Hieu"]},
            "port_selection": {"status": "candidate_for_validation", "min_active_share": 0.2,
                               "min_cargo_coverage": 1.0, "activity_group_cuts": [1/3, 2/3]},
        }

    def test_hand_worked_windows_and_port_isolation(self):
        frame = validation_table(self.panel, self.config)
        day = frame.loc[frame.date.eq("2020-01-28")].set_index("port_id")
        self.assertEqual(day.loc["A", "cargo_7d"], sum(range(22, 29)))
        self.assertEqual(day.loc["A", "cargo_mean_28d"], 14.5)
        self.assertEqual(day.loc["A", "calls_7d"], sum(i % 3 for i in range(22, 29)))
        self.assertEqual(day.loc["A", "y_true"], sum(range(29, 36)))
        self.assertEqual(day.loc["B", "y_true"], 100 * sum(range(29, 36)))
        self.assertEqual(day.loc["A", "split"], "train")

    def test_label_boundaries_and_validation_anchor(self):
        frame = validation_table(self.panel, self.config)
        a = frame.loc[frame.port_id.eq("A")].set_index("date")
        self.assertEqual(a.loc["2020-02-22", "split"], "train")
        self.assertEqual(a.loc["2020-02-23":"2020-02-28", "split"].tolist(), ["excluded"] * 6)
        self.assertEqual(a.loc["2020-02-29", "split"], "validation")
        self.assertEqual(a.loc["2020-02-29", "target_start"], pd.Timestamp("2020-03-01"))
        self.assertEqual(a.loc["2020-03-24", "target_end"], pd.Timestamp("2020-03-31"))
        self.assertEqual(a.loc["2020-03-25", "split"], "excluded")
        self.assertEqual(a.loc["2020-03-31", "exclusion_reason"], "origin_reserved_for_test")
        self.assertTrue(frame.loc[frame.split.eq("validation"), "target_start"].gt(pd.Timestamp(self.config["train_end"])).all())
        self.assertTrue(frame.loc[frame.split.eq("train"), "target_end"].le(pd.Timestamp(self.config["train_end"])).all())

    def test_test_measurements_cannot_change_windows_or_candidates(self):
        before = validation_table(self.panel, self.config)
        candidates_before = candidate_lists(self.panel, self.config)
        changed = self.panel.copy()
        changed.loc[changed.date.gt(self.config["validation_end"]), ["cargo_tonnes", "portcalls"]] = np.nan
        assert_frame_equal(before, validation_table(changed, self.config))
        for name, original in candidates_before.items():
            assert_frame_equal(original, candidate_lists(changed, self.config)[name])
        self.assertTrue(before.date.le(pd.Timestamp(self.config["validation_end"])).all())

    def test_missing_history_is_unknown_and_never_a_zero(self):
        changed = self.panel.copy()
        changed.loc[changed.port_id.eq("A") & changed.date.eq("2020-02-28"), "cargo_tonnes"] = np.nan
        result = validation_table(changed, self.config)
        a = result.loc[result.port_id.eq("A") & result.date.eq("2020-02-29")].iloc[0]
        self.assertTrue(pd.isna(a.cargo_7d))
        self.assertFalse(a.window_complete)
        self.assertEqual(a.exclusion_reason, "incomplete_past_window")
        b = result.loc[result.port_id.eq("B") & result.date.eq("2020-02-29")].iloc[0]
        self.assertTrue(b.window_complete)
        candidates = candidate_lists(changed, self.config)
        self.assertFalse(candidates["active_20pct"].set_index("port_id").loc["A", "selected"])

    def test_missing_calendar_record_is_rejected_before_rolling(self):
        with self.assertRaisesRegex(ValueError, "daily calendars"):
            validation_table(self.panel.drop(index=1), self.config)

    def test_metrics_match_hand_calculation_and_zero_denominator(self):
        frame = pd.DataFrame({"port_id": ["A", "A", "B"], "y_true": [0, 10, 10], "y_pred": [2, 8, 13]})
        result = metrics(frame)
        self.assertAlmostEqual(result["MAE"], 7/3)
        self.assertAlmostEqual(result["RMSE"], np.sqrt(17/3))
        self.assertAlmostEqual(result["WAPE_pct"], 35)
        self.assertAlmostEqual(result["macro_port_MAE"], 2.5)
        self.assertEqual(result["zero_actual_windows"], 1)
        frame["y_true"] = 0
        self.assertIsNone(metrics(frame)["WAPE_pct"])

    def test_scaling_is_fit_on_training_and_fixed_regression_is_recovered(self):
        rng = np.random.default_rng(42)
        training = pd.DataFrame(rng.normal(size=(20, 3)), columns=FEATURES)
        training["y_true"] = 7 + training[FEATURES].to_numpy() @ np.array([2, -3, 5])
        evaluation = pd.DataFrame([[10, 20, 30], [-4, 6, 8]], columns=FEATURES)
        result, settings = fit_linear(training, evaluation)
        np.testing.assert_allclose(result, 7 + evaluation.to_numpy() @ np.array([2, -3, 5]))
        np.testing.assert_allclose(settings["training_mean"], training[FEATURES].mean())
        _, other = fit_linear(training, evaluation * 1000)
        self.assertEqual(settings, other)


@unittest.skipUnless((ROOT / "results/eligibility_validation.json").exists(), "Run validation sensitivity to enable artifact reconciliation")
class ValidationArtifactChecks(unittest.TestCase):
    def test_real_predictions_use_identical_keys_and_reconcile_with_report(self):
        results = ROOT / "results"
        audit = json.loads((results / "eligibility_validation.json").read_text(encoding="utf-8"))
        self.assertFalse(audit["frozen"])
        self.assertFalse(audit["test_scored"])
        self.assertEqual(sha256(ROOT / "src/validate_port_rules.py"), audit["script_sha256"])
        self.assertEqual(sha256(ROOT / "src/prepare_data.py"), audit["preparation_script_sha256"])
        self.assertEqual(sha256(ROOT / "data/ports_daily.csv"), audit["panel_sha256"])
        keys = pd.read_csv(results / "eligibility_validation_keys.csv")
        self.assertEqual(sha256(results / "eligibility_validation_keys.csv"), audit["common_keys_sha256"])
        for rule in audit["config"]["candidates"]:
            predictions = pd.read_csv(results / f"eligibility_validation_predictions_{rule}.csv")
            self.assertEqual(predictions.columns.tolist(), ["model", "feature_set", "split", "port_id", "country_iso3", "origin_date", "target_start", "target_end", "y_true", "y_pred"])
            self.assertTrue(predictions.split.eq("validation").all())
            for model, sample in predictions.groupby("model", sort=True):
                sample = sample.reset_index(drop=True)
                assert_frame_equal(sample[keys.columns], keys)
                origin = pd.to_datetime(sample.origin_date)
                self.assertTrue(pd.to_datetime(sample.target_start).eq(origin + pd.Timedelta(days=1)).all())
                self.assertTrue(pd.to_datetime(sample.target_end).eq(origin + pd.Timedelta(days=7)).all())
                self.assertTrue(sample.target_start.gt(audit["config"]["train_end"]).all())
                self.assertTrue(sample.target_end.le(audit["config"]["validation_end"]).all())
                expected = next(m for m in audit["metrics"] if m["eligibility_rule"] == rule and m["model"] == model)
                measured = metrics(sample)
                for metric in ["MAE", "RMSE", "WAPE_pct", "macro_port_MAE"]:
                    self.assertAlmostEqual(measured[metric], expected[metric], places=7)
        original = json.loads((ROOT / "experiment.json").read_text(encoding="utf-8"))
        for field in ["train_start", "train_end", "validation_end", "test_end", "data_snapshot_sha256"]:
            self.assertEqual(original[field], audit["config"][field])


if __name__ == "__main__":
    unittest.main()
