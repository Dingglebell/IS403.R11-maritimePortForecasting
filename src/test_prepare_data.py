"""Focused Task 1 checks; no Task 2 feature/model results are claimed."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from prepare_data import clean_daily_panel, load_snapshot, select_ports, zero_runs

REPO_ROOT = Path(__file__).resolve().parents[1]


def source_row(port, day, inbound=0, outbound=0, calls=0):
    return {"date": f"2020-01-{day:02d} 00:00:00+00:00", "portid": port,
            "ISO3": "VNM", "import": inbound, "export": outbound, "portcalls": calls}


def agreement():
    return {
        "train_end": "2020-01-05", "validation_end": "2020-01-07", "test_end": "2020-01-09",
        "time_split_agreement": {"status": "agreed", "agreed_by": ["Dinh", "Hieu"]},
        "port_selection": {"status": "candidate_agreed_for_validation", "min_active_share": 0.2,
                           "min_cargo_coverage": 0.6, "activity_group_cuts": [1/3, 2/3]},
    }


class PanelChecks(unittest.TestCase):
    def test_missing_calendar_day_and_missing_component_are_not_zero(self):
        raw = pd.DataFrame([source_row("A", 1), source_row("A", 3, np.nan, 10), source_row("B", 1, 100, 20), source_row("B", 3, 200, 30)])
        panel, gaps = clean_daily_panel(raw)
        a = panel.loc[panel.port_id.eq("A")].reset_index(drop=True)
        self.assertEqual(len(panel), 6)
        self.assertEqual(len(gaps), 2)
        self.assertEqual(a.loc[0, "cargo_tonnes"], 0)
        self.assertTrue(pd.isna(a.loc[1, "cargo_tonnes"]))
        self.assertTrue(pd.isna(a.loc[1, "portcalls"]))
        self.assertTrue(pd.isna(a.loc[2, "cargo_tonnes"]))
        self.assertEqual(panel.loc[panel.port_id.eq("B"), "cargo_tonnes"].iloc[0], 120)

    def test_missing_dates_break_zero_runs_and_ports_are_isolated(self):
        raw = pd.DataFrame([source_row("A", 1, calls=2), source_row("A", 3), source_row("A", 4), source_row("A", 5, 1),
                            *[source_row("B", day) for day in range(1, 6)]])
        panel, _ = clean_daily_panel(raw)
        runs = zero_runs(panel)
        self.assertEqual(runs.loc[runs.port_id.eq("A"), "days"].tolist(), [1, 2])
        self.assertEqual(runs.loc[runs.port_id.eq("A"), "days_with_positive_calls"].tolist(), [1, 0])
        self.assertEqual(runs.loc[runs.port_id.eq("B"), "days"].tolist(), [5])

    def test_duplicate_or_missing_keys_require_investigation(self):
        one = source_row("A", 1)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            clean_daily_panel(pd.DataFrame([one, one]))
        one["portid"] = " "
        with self.assertRaisesRegex(ValueError, "Missing key"):
            clean_daily_panel(pd.DataFrame([one]))

    def test_invalid_numeric_values_and_incompatible_countries_are_rejected(self):
        for column, value in [("import", -1), ("export", "bad"), ("import", np.inf), ("portcalls", 0.5)]:
            with self.subTest(column=column, value=value):
                one = source_row("A", 1)
                one[column] = value
                with self.assertRaises(ValueError):
                    clean_daily_panel(pd.DataFrame([one]))
        raw = pd.DataFrame([source_row("A", 1), source_row("A", 2)])
        raw.loc[1, "ISO3"] = "SGP"
        with self.assertRaisesRegex(ValueError, "multiple countries"):
            clean_daily_panel(raw)

    def test_non_midnight_and_unknown_dates_are_rejected(self):
        for value in [None, "2020-01-01T06:00:00Z", "not-a-date"]:
            one = source_row("A", 1)
            one["date"] = value
            with self.subTest(date=value), self.assertRaises((ValueError, TypeError)):
                clean_daily_panel(pd.DataFrame([one]))

    def test_source_aggregates_are_used_once_and_output_is_sorted(self):
        raw = pd.DataFrame([source_row("A", 2, 100, 20), source_row("A", 1, 50, 10)])
        raw["import_cargo"] = 100
        raw["export_cargo"] = 20
        panel, _ = clean_daily_panel(raw)
        self.assertEqual(panel.cargo_tonnes.tolist(), [60, 120])
        self.assertEqual(panel.columns.tolist(), ["date", "port_id", "country_iso3", "import_tonnes", "export_tonnes", "portcalls", "cargo_tonnes"])

    def test_no_zero_runs_is_a_valid_empty_result(self):
        panel, _ = clean_daily_panel(pd.DataFrame([source_row("A", 1, 10)]))
        runs = zero_runs(panel)
        self.assertTrue(runs.empty)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(runs.start_date))


class TrainingSelectionChecks(unittest.TestCase):
    def setUp(self):
        raw = pd.DataFrame([
            source_row("A", 1, 100), source_row("A", 2), source_row("A", 3),
            *[source_row("A", day, 1_000_000) for day in range(6, 10)],
            *[source_row("B", day, 10) for day in range(6, 10)],
        ])
        self.panel, _ = clean_daily_panel(raw)

    def test_future_observations_cannot_change_selection_or_groups(self):
        before = select_ports(self.panel, agreement())
        changed = self.panel.copy()
        future = changed.date.gt(pd.Timestamp("2020-01-05"))
        changed.loc[future, ["import_tonnes", "export_tonnes", "cargo_tonnes"]] = 0
        after = select_ports(changed, agreement())
        assert_frame_equal(before, after)
        a = before.loc[before.port_id.eq("A")].iloc[0]
        b = before.loc[before.port_id.eq("B")].iloc[0]
        self.assertAlmostEqual(a.train_coverage, 3/5)
        self.assertAlmostEqual(a.train_active_share, 1/5)
        self.assertAlmostEqual(a.train_active_share_observed, 1/3)
        self.assertTrue(a.selected)
        self.assertFalse(b.selected)
        self.assertEqual(b.reason, "no_observed_training_cargo")
        self.assertTrue(pd.isna(b.activity_group))

    def test_selection_requires_team_agreement_and_complete_cutoffs(self):
        for config in [{}, {**agreement(), "train_end": None}, {**agreement(), "time_split_agreement": {"status": "proposed", "agreed_by": ["Dinh", "Hieu"]}}]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                select_ports(self.panel, config)

    def test_bad_order_and_invalid_thresholds_are_rejected(self):
        bad = agreement()
        bad["validation_end"] = bad["train_end"]
        with self.assertRaisesRegex(ValueError, "chronological"):
            select_ports(self.panel, bad)
        for cuts in [[], [0.8, 0.2]]:
            bad = agreement()
            bad["port_selection"]["activity_group_cuts"] = cuts
            with self.assertRaisesRegex(ValueError, "thresholds"):
                select_ports(self.panel, bad)


class SnapshotChecks(unittest.TestCase):
    def test_changed_raw_bytes_are_rejected(self):
        repo_root = Path(__file__).resolve().parents[1]
        temp_root = repo_root / "results"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="task1-check-", dir=temp_root) as folder:
            work = Path(folder).resolve()
            self.assertTrue(work.is_relative_to(repo_root))
            source = work / "viet-nam.csv"
            pd.DataFrame([source_row("A", 1)]).to_csv(source, index=False)
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest = work / "snapshot.json"
            manifest.write_text(json.dumps({"files": [{"country": "viet-nam", "file": str(source), "sha256": digest}]}), encoding="utf-8")
            self.assertEqual(len(load_snapshot(manifest)[0]), 1)
            source.write_bytes(source.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                load_snapshot(manifest)


@unittest.skipUnless((REPO_ROOT / "data/ports_daily.csv").exists() and (REPO_ROOT / "results/data_audit.json").exists(),
                     "Run Task 1 preparation to enable real-snapshot reconciliation")
class RealSnapshotChecks(unittest.TestCase):
    @unittest.skipUnless((REPO_ROOT / "data/selected_ports.csv").exists(), "Run --select-ports to check candidate outputs")
    def test_selected_ports_reconcile_with_independent_training_counts(self):
        config = json.loads((REPO_ROOT / "experiment.json").read_text(encoding="utf-8"))
        panel = pd.read_csv(REPO_ROOT / "data/ports_daily.csv", parse_dates=["date"])
        training = panel.loc[panel.date.between(config["train_start"], config["train_end"])].copy()
        training["active"] = training.cargo_tonnes.gt(0)
        stats = training.groupby("port_id").agg(known=("cargo_tonnes", "count"), active=("active", "sum"))
        days = (pd.Timestamp(config["train_end"]) - pd.Timestamp(config["train_start"])).days + 1
        rule = config["port_selection"]
        included = stats.index[(stats.known / days >= rule["min_cargo_coverage"]) & (stats.active / days >= rule["min_active_share"])]
        selected = pd.read_csv(REPO_ROOT / "data/selected_ports.csv").set_index("port_id")
        self.assertEqual(set(selected.index), set(included))
        self.assertTrue(selected.selected.all())
        self.assertTrue(selected.train_calendar_days.eq(days).all())
        self.assertTrue(selected.train_observed_cargo_days.eq(stats.loc[selected.index, "known"]).all())
        self.assertTrue(selected.train_active_days.eq(stats.loc[selected.index, "active"]).all())
        np.testing.assert_allclose(selected.train_active_share, stats.loc[selected.index, "active"] / days)
        shares = stats.loc[selected.index, "active"] / days
        low, high = rule["activity_group_cuts"]
        expected_groups = np.where(shares < low, "low", np.where(shares < high, "medium", "high"))
        self.assertEqual(selected.activity_group.tolist(), expected_groups.tolist())
        retention = pd.read_csv(REPO_ROOT / "results/country_retention.csv").set_index("country_iso3")
        self.assertTrue(retention.retained_ports.eq(selected.groupby("country_iso3").size()).all())
        self.assertEqual(int(retention.excluded_ports.sum()), len(stats) - len(selected))
        rules = json.loads((REPO_ROOT / "results/port_selection_rules.json").read_text(encoding="utf-8"))
        self.assertFalse(rules["frozen"])
        self.assertEqual(rules["rule"], rule)

    def test_export_matches_every_original_observation_and_recorded_hash(self):
        snapshot = json.loads((REPO_ROOT / "data/raw/hdx_2026-10-18/snapshot.json").read_text(encoding="utf-8"))
        audit = json.loads((REPO_ROOT / "results/data_audit.json").read_text(encoding="utf-8"))
        frames = []
        for record in snapshot["files"]:
            path = REPO_ROOT / record["file"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])
            frames.append(pd.read_csv(path, usecols=["date", "portid", "ISO3", "portname", "import", "export", "portcalls"],
                                      dtype={"portid": "string", "ISO3": "string"}))
        raw = pd.concat(frames, ignore_index=True)
        reference = pd.DataFrame({
            "date": raw["date"].str.slice(0, 10), "port_id": raw["portid"], "country_iso3": raw["ISO3"],
            "import_tonnes": raw["import"], "export_tonnes": raw["export"],
            "portcalls": raw["portcalls"], "cargo_tonnes": raw["import"] + raw["export"],
        }).sort_values(["port_id", "date"]).reset_index(drop=True)
        panel_path = REPO_ROOT / "data/ports_daily.csv"
        actual = pd.read_csv(panel_path, dtype={"port_id": "string", "country_iso3": "string"})
        assert_frame_equal(actual, reference, check_dtype=False, check_exact=True)
        self.assertFalse(actual.duplicated(["port_id", "date"]).any())
        differences = pd.to_datetime(actual["date"]).groupby(actual["port_id"]).diff().dropna()
        self.assertTrue(differences.eq(pd.Timedelta(days=1)).all())
        self.assertEqual(len(actual), audit["raw_rows"])
        self.assertEqual(hashlib.sha256(panel_path.read_bytes()).hexdigest(), audit["panel_sha256"])
        self.assertEqual(hashlib.sha256((REPO_ROOT / "src/prepare_data.py").read_bytes()).hexdigest(), audit["preparation_script_sha256"])
        public = json.loads((REPO_ROOT / "docs/portwatch_snapshot_manifest.json").read_text(encoding="utf-8"))
        experiment = json.loads((REPO_ROOT / "experiment.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["data_snapshot_sha256"], public["bundle_sha256"])
        self.assertEqual(audit["data_snapshot_sha256"], experiment["data_snapshot_sha256"])
        labels = raw.assign(label=raw["portname"].str.contains("Offshore Oil Terminal", case=False, regex=False)).groupby("portid")["label"].any()
        metadata = pd.read_csv(REPO_ROOT / "data/ports_metadata.csv").set_index("port_id")
        self.assertTrue(metadata["source_named_offshore_oil_terminal"].eq(metadata.index.to_series().map(labels)).all())
        self.assertEqual(int(labels.sum()), audit["source_named_offshore_oil_terminal_ids"])


if __name__ == "__main__":
    unittest.main()
