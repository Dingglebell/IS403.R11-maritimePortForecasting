import unittest

import pandas as pd

from evaluate import align_forecasts, reference_rows, score


class EvaluationChecks(unittest.TestCase):
    def setUp(self):
        self.config = {"train_end": "2024-12-31", "validation_end": "2025-12-31", "test_end": "2026-10-02"}
        self.table = pd.DataFrame({"port_id": ["A", "A", "B"], "country_iso3": ["VNM", "VNM", "SGP"],
                                   "activity_group": ["low", "low", "high"], "split": "validation",
                                   "origin_date": ["2024-12-31", "2025-01-01", "2024-12-31"],
                                   "target_start": ["2025-01-01", "2025-01-02", "2025-01-01"],
                                   "target_end": ["2025-01-07", "2025-01-08", "2025-01-07"],
                                   "target_7d": [0., 10., 40.]})
        self.reference = reference_rows(self.table, self.config, "validation")
        self.forecasts = self.table.drop(columns="activity_group").rename(columns={"target_7d": "y_true"})
        self.forecasts = self.forecasts.assign(model="forest", feature_set="cargo_only", y_pred=[2., 10., 34.])

    def test_scores_keep_variants_separate_and_wape_uses_total_actual(self):
        second = self.forecasts.assign(feature_set="all_three", y_pred=[0., 10., 40.])
        aligned, coverage = align_forecasts(pd.concat([second, self.forecasts]), self.reference, "validation")
        scores, _ = score(aligned, "all_eligible")
        overall = scores.loc[scores.group_type.eq("overall")].set_index("feature_set")
        self.assertEqual(len(coverage), 2)
        self.assertAlmostEqual(overall.loc["cargo_only", "MAE"], 8 / 3)
        self.assertAlmostEqual(overall.loc["cargo_only", "macro_port_MAE"], 3.5)
        self.assertAlmostEqual(overall.loc["cargo_only", "RMSE"], (40 / 3) ** 0.5)
        self.assertAlmostEqual(overall.loc["cargo_only", "WAPE_pct"], 16.)
        self.assertEqual(overall.loc["all_three", "MAE"], 0.)
        zero = scores.loc[scores.group_type.eq("actual_volume") & scores.group.eq("zero")]
        self.assertTrue(zero.WAPE_pct.isna().all())
        phase = scores.loc[scores.group_type.eq("weekly_phase") & scores.feature_set.eq("cargo_only")]
        self.assertEqual(dict(zip(phase.group, phase.n_rows)), {0: 2, 1: 1})

    def test_incomplete_duplicate_or_misaligned_forecasts_cannot_be_scored(self):
        for bad in [self.forecasts.iloc[:-1], pd.concat([self.forecasts, self.forecasts.iloc[:1]]),
                    self.forecasts.assign(y_true=[1., 10., 40.]), self.forecasts.assign(y_pred=[-1., 10., 40.]),
                    self.forecasts.assign(target_end="2025-01-07")]:
            with self.subTest(), self.assertRaisesRegex(ValueError, "Correct the reported rows"):
                align_forecasts(bad, self.reference, "validation")

    def test_subset_comparison_accepts_full_and_subset_forecasts_for_the_same_keys(self):
        extension = self.forecasts.loc[self.forecasts.port_id.eq("B")].assign(model="sarima")
        forecasts = pd.concat([self.forecasts, extension])
        with self.assertRaises(ValueError):
            align_forecasts(forecasts, self.reference, "validation")
        aligned, coverage = align_forecasts(forecasts, self.reference, "validation", "high")
        self.assertEqual(aligned.port_id.tolist(), ["B", "B"])
        self.assertEqual(coverage.matched_rows.tolist(), [1, 1])

    def test_validation_target_cannot_cross_into_test(self):
        table = self.table.iloc[:1].assign(origin_date="2025-12-25", target_start="2025-12-26", target_end="2026-01-01")
        with self.assertRaisesRegex(ValueError, "outside the validation window"):
            reference_rows(table, self.config, "validation")


if __name__ == "__main__":
    unittest.main()
