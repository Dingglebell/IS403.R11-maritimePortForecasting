"""Run Task 1 checks and record a verification receipt; no skipped checks allowed."""

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from prepare_data import sha256, write_json


def test_names(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_names(item)
        else:
            yield item.id()


def main():
    root = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(root / "src"), pattern="test_*.py")
    names = list(test_names(suite))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:
        print("Verification not recorded: fix failures or run preparation and validation to enable all integration checks.", file=sys.stderr)
        return 1
    audit = json.loads((root / "results/data_audit.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "results/eligibility_validation.json").read_text(encoding="utf-8"))
    selected = pd.read_csv(root / "data/selected_ports.csv")
    integration = [name for name in names if ".RealSnapshotChecks." in name or ".ValidationArtifactChecks." in name]
    receipt = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(), "status": "passed",
        "test_command": "python src/verify_task1.py", "test_names": names,
        "total_tests_passed": result.testsRun, "unit_tests_passed": result.testsRun - len(integration),
        "real_snapshot_integration_tests_passed": len(integration), "skipped_tests": 0,
        "source_hashes_rechecked": len(audit["source_files"]), "raw_to_panel_rows_matched": audit["panel_rows"],
        "ports": audit["ports"], "calendar_days_per_port": audit["calendar_days"],
        "source_and_output_hashes_match_audit": True, "sorted_unique_daily_keys": True,
        "selection_run": audit["selection_run"], "selected_candidate_ports": len(selected),
        "selected_countries": int(selected.country_iso3.nunique()),
        "activity_groups": {str(k): int(v) for k, v in selected.activity_group.value_counts().sort_index().items()},
        "source_named_offshore_terminal_ids_verified": audit["source_named_offshore_oil_terminal_ids"],
        "panel_sha256": audit["panel_sha256"], "selected_ports_sha256": sha256(root / "data/selected_ports.csv"),
        "preparation_script_sha256": audit["preparation_script_sha256"],
        "validation_script_sha256": validation["script_sha256"], "verification_script_sha256": sha256(__file__),
        "common_validation_keys_sha256": validation["common_keys_sha256"],
        "common_validation_rows": validation["common_validation_rows"], "test_scored": False, "rules_frozen": False,
        "remaining": ["Joint Task 2 review of eligibility comparison and information cutoff",
                      "Final shared eligibility decision and rule freeze before test scoring",
                      "Peer review through the repository branch/PR workflow"],
    }
    write_json(root / "results/task1_verification.json", receipt)
    print(json.dumps({k: receipt[k] for k in ["status", "total_tests_passed", "selected_candidate_ports", "test_scored", "rules_frozen"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
