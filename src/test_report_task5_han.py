"""Guards against mixing sensitivity variants or silently changing report evidence."""
import unittest
import numpy as np
import pandas as pd
from report_task5_han import compare_metrics, primary_metrics, relative_metrics, KEY, VALUES


def metrics():
    rows = []
    for model, mae in [("seasonal_naive", 10.), ("linear_multivariate", 8.)]:
        rows.append(dict(zip(KEY, [model, "cargo_only", "test", "all_eligible", "overall", "all"]),
            **dict(zip(VALUES, [10, 2, 0, mae, 12, 20, mae, 1]))))
    return pd.DataFrame(rows)


class ReportChecks(unittest.TestCase):
    def test_relative_error_and_zero_denominator(self):
        m = metrics()
        r = relative_metrics(m)
        self.assertAlmostEqual(r.loc[r.model.eq("linear_multivariate"), "MAE_change_vs_naive_pct"].item(), -20)
        m["MAE"] = 0.
        r = relative_metrics(m)
        self.assertTrue(r.MAE_change_vs_naive_pct.isna().all())
        self.assertFalse(r.beats_naive_MAE.any())

    def test_all_metric_keys_and_values_verified(self):
        m = metrics()
        compare_metrics(m.iloc[::-1], m)
        changed = m.copy(); changed.loc[0, "MAE"] += 1
        with self.assertRaises(AssertionError): compare_metrics(changed, m)
        changed = m.copy(); changed.loc[0, "group"] = "other"
        with self.assertRaises(AssertionError): compare_metrics(changed, m)
        with self.assertRaises(AssertionError): compare_metrics(m.iloc[:1], m)

    def test_undefined_wape_preserved(self):
        m = metrics(); m["WAPE_pct"] = np.nan
        compare_metrics(m, m)
        bad = m.copy(); bad["WAPE_pct"] = 0
        with self.assertRaises(AssertionError): compare_metrics(bad, m)

    def test_primary_design_rejects_relabelled_sensitivity(self):
        m = metrics()
        s = m[["model", "feature_set"]].assign(primary_comparison=True)
        freeze = {"primary_comparison": ["seasonal_naive/cargo_only", "linear_multivariate/cargo_only"]}
        self.assertEqual(len(primary_metrics(m, s, freeze)), 2)
        s.loc[1, "feature_set"] = "test_selected"
        with self.assertRaises(ValueError): primary_metrics(m, s, freeze)


if __name__ == "__main__":
    unittest.main()
