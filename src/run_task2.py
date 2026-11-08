"""Run Task 2 features, four baselines and validation exports in one command."""

import argparse
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from features import export_features, sha256
from baselines import export_baselines


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--panel", type=Path, default=Path("data/ports_daily.csv"))
    p.add_argument("--experiment", type=Path, default=Path("experiment.json"))
    p.add_argument("--table", type=Path, default=Path("data/learning_table.csv"))
    p.add_argument("--results-dir", type=Path, default=Path("results"))
    p.add_argument("--clipping", choices=["none", "nonnegative"], default=None)
    a = p.parse_args()
    config = json.loads(a.experiment.read_text(encoding="utf-8"))
    task1_record = Path("results/task1_run.json")
    if not task1_record.exists():
        p.error("Run from the repository root; results/task1_run.json is required")
    if not a.panel.is_file():
        p.error(f"Missing clean panel: {a.panel}. Obtain Hân's handoff or run src/prepare_data.py first")
    expected_hash = json.loads(task1_record.read_text(encoding="utf-8"))["panel_sha256"]
    actual_hash = sha256(a.panel)
    if actual_hash != expected_hash:
        p.error("Panel differs from Task 1's reviewed snapshot; audit a new snapshot before use")
    table = export_features(a.panel, a.experiment, a.table, a.results_dir)
    predictions, scores, _ = export_baselines(table, config, a.results_dir, a.clipping)
    keys = table.loc[table.split.eq("validation"), ["port_id", "origin_date", "target_start", "target_end"]]
    keys_path = a.results_dir / "task2_validation_keys.csv"
    keys.to_csv(keys_path, index=False, date_format="%Y-%m-%d", lineterminator="\n")
    record = {
        "status": "validation_pipeline_run; shared_rule_freeze_pending", "test_scored": False,
        "panel_sha256": actual_hash, "experiment_sha256": sha256(a.experiment),
        "learning_table_sha256": sha256(a.table), "validation_keys_sha256": sha256(keys_path),
        "clipping_in_working_output": predictions.clipping.iloc[0],
        "clipping_configured": config.get("clip_negative_predictions"),
        "cohort_rule": config["port_selection"]["handoff_rule"],
        "cohort_status": config["port_selection"]["status"],
        "train_rows": int(table.split.eq("train").sum()),
        "validation_rows_per_model": len(keys), "ports": int(keys.port_id.nunique()),
        "cutoffs": {k: config[k] for k in ["train_start", "train_end", "validation_end", "test_end"]},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "code_sha256": {name: sha256(Path(__file__).with_name(name))
                        for name in ["features.py", "baselines.py", "run_task2.py"]},
    }
    (a.results_dir / "task2_run.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Task 2 pipeline complete. Test untouched. Review cohort and clipping before freezing shared rules.")


if __name__ == "__main__":
    main()
