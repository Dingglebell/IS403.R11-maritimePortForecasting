"""Checks for the daily-panel cleaning contract."""

import unittest

import pandas as pd

from prepare_data import clean_daily_panel


def row(port="A", day=1, inbound=0, outbound=0, calls=0):
    return {"date": f"2020-01-{day:02d}T00:00:00Z", "portid": port, "ISO3": "VNM",
            "import": inbound, "export": outbound, "portcalls": calls}


class CleaningChecks(unittest.TestCase):
    def test_schema_sorting_and_no_double_counting(self):
        raw = pd.DataFrame([row(day=2, inbound="100", outbound="20"), row(inbound="50", outbound="10")])
        raw["import_cargo"] = 1000
        raw["export_cargo"] = 2000
        panel = clean_daily_panel(raw)
        self.assertEqual(panel.columns.tolist(), ["date", "port_id", "country_iso3", "import_tonnes", "export_tonnes", "portcalls", "cargo_tonnes"])
        self.assertEqual(panel.cargo_tonnes.tolist(), [60, 120])
        self.assertEqual(panel.date.dt.strftime("%Y-%m-%d").tolist(), ["2020-01-01", "2020-01-02"])

    def test_calendar_gaps_and_unknown_components_are_distinct_from_zero(self):
        raw = pd.DataFrame([row(), row(day=3, inbound=float("nan"), outbound=10),
                            row("B", inbound=100), row("B", day=3, inbound=200)])
        panel = clean_daily_panel(raw)
        a = panel.loc[panel.port_id.eq("A")].reset_index(drop=True)
        self.assertEqual(len(panel), 6)
        self.assertEqual(a.loc[0, "cargo_tonnes"], 0)
        self.assertTrue(pd.isna(a.loc[1, "cargo_tonnes"]))
        self.assertTrue(pd.isna(a.loc[1, "portcalls"]))
        self.assertTrue(pd.isna(a.loc[2, "cargo_tonnes"]))
        self.assertTrue(a.country_iso3.eq("VNM").all())
        self.assertEqual(panel.loc[panel.port_id.eq("B"), "cargo_tonnes"].iloc[0], 100)

    def test_duplicate_normalized_keys_are_not_silently_dropped(self):
        first, second = row(), row(port=" A ")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            clean_daily_panel(pd.DataFrame([first, second]))

    def test_missing_keys_and_country_conflicts_are_rejected(self):
        for value in [None, " "]:
            one = row(port=value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Missing key"):
                clean_daily_panel(pd.DataFrame([one]))
        raw = pd.DataFrame([row(), row(day=2)])
        raw.loc[1, "ISO3"] = "SGP"
        with self.assertRaisesRegex(ValueError, "multiple countries"):
            clean_daily_panel(raw)
        raw.loc[1, "ISO3"] = "vn"
        with self.assertRaisesRegex(ValueError, "ISO3"):
            clean_daily_panel(raw)

    def test_invalid_values_and_fractional_calls_are_rejected(self):
        for column, value in [("import", -1), ("export", "bad"), ("import", float("inf")),
                              ("export", -float("inf")), ("portcalls", 0.5)]:
            one = row()
            one[column] = value
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                clean_daily_panel(pd.DataFrame([one]))

    def test_unknown_non_midnight_or_invalid_dates_are_rejected(self):
        for value in [None, "2020-01-01T06:00:00Z", "not-a-date"]:
            one = row()
            one["date"] = value
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                clean_daily_panel(pd.DataFrame([one]))

    def test_empty_input_and_missing_columns_are_rejected(self):
        for raw in [pd.DataFrame(), pd.DataFrame([row()]).drop(columns="import")]:
            with self.assertRaises(ValueError):
                clean_daily_panel(raw)


if __name__ == "__main__":
    unittest.main()
