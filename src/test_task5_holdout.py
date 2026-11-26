import unittest

import numpy as np
import pandas as pd

from features import FEATURES
from run_task5_test import build_test_windows


class HoldoutWindows(unittest.TestCase):
    def setUp(self):
        self.config = {"horizon_days": 7, "history_days": [7, 28], "train_start": "2019-01-01",
                       "train_end": "2024-12-31", "validation_end": "2025-12-31", "test_end": "2026-01-12",
                       "port_selection": {"handoff_rule": "complete_training_coverage"}, "pool_ports": True,
                       "refit_before_test": False, "clip_negative_predictions": True}
        self.ports = pd.DataFrame({"port_id": ["A", "B"], "country_iso3": ["VNM", "IDN"],
                                   "activity_group": ["high", "low"], "selected": [True, True]})
        dates = pd.date_range("2025-12-04", "2026-01-12")
        self.panel = pd.concat([
            pd.DataFrame({"port_id": "A", "date": dates, "cargo_tonnes": np.arange(len(dates)), "portcalls": 3}),
            pd.DataFrame({"port_id": "B", "date": dates, "cargo_tonnes": 0, "portcalls": 0})
        ], ignore_index=True)

    def test_boundary_labels_and_history_are_anchored_to_each_origin(self):
        table, exclusions = build_test_windows(self.panel, self.ports, self.config)
        first = table.loc[table.port_id.eq("A")].iloc[0]
        self.assertEqual(len(table), 12)
        self.assertTrue(exclusions.empty)
        self.assertEqual((first.origin_date, first.target_start, first.target_end),
                         ("2025-12-31", "2026-01-01", "2026-01-07"))
        self.assertEqual(table.target_end.max(), "2026-01-12")
        self.assertEqual((first.cargo_7d, first.calls_7d, first.cargo_mean_28d, first.target_7d),
                         (168, 21, 13.5, 217))
        self.assertTrue(table.loc[table.port_id.eq("B"), "target_7d"].eq(0).all())

        later = self.panel.copy()
        later.loc[later.port_id.eq("A") & later.date.eq("2026-01-01"), "cargo_tonnes"] += 1_000
        changed, _ = build_test_windows(later, self.ports, self.config)
        first_changed = changed.loc[changed.port_id.eq("A")].iloc[0]
        pd.testing.assert_series_equal(first[FEATURES], first_changed[FEATURES])
        self.assertEqual(first_changed.target_7d, first.target_7d + 1_000)

    def test_absent_day_remains_missing_and_is_counted(self):
        panel = self.panel.loc[~(self.panel.port_id.eq("A") & self.panel.date.eq("2026-01-01"))]
        table, exclusions = build_test_windows(panel, self.ports, self.config)
        first = exclusions.loc[exclusions.origin_date.eq("2025-12-31")].iloc[0]
        self.assertEqual(first.port_id, "A")
        self.assertTrue(first.incomplete_target)
        self.assertFalse(first.incomplete_history)
        self.assertEqual(len(table) + len(exclusions), 12)
        self.assertTrue(table.port_id.eq("B").all())


if __name__ == "__main__":
    unittest.main()
