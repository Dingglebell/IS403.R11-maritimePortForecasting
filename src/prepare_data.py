"""Clean raw PortWatch CSV files into the repository's daily port schema."""

import argparse
from math import isfinite
from pathlib import Path

import pandas as pd


SOURCE_MAP = {
    "date": "date", "portid": "port_id", "ISO3": "country_iso3",
    "import": "import_tonnes", "export": "export_tonnes", "portcalls": "portcalls",
}
PANEL_COLUMNS = [*SOURCE_MAP.values(), "cargo_tonnes"]


def read_raw_files(input_dir):
    files = sorted(Path(input_dir).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No raw CSV files found in {input_dir}")
    frames = []
    for path in files:
        frame = pd.read_csv(path, usecols=lambda column: column in SOURCE_MAP,
                            dtype={"portid": "string", "ISO3": "string"})
        missing = set(SOURCE_MAP) - set(frame.columns)
        if missing or frame.empty:
            raise ValueError(f"{path.name}: empty data or missing columns {sorted(missing)}")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def clean_daily_panel(raw):
    """Preserve reported zeros and unknown values; stop on ambiguous records."""
    missing = set(SOURCE_MAP) - set(raw.columns)
    if missing or raw.empty:
        raise ValueError(f"Empty data or missing required source columns: {sorted(missing)}")
    frame = raw[list(SOURCE_MAP)].rename(columns=SOURCE_MAP).copy()
    for column in ["port_id", "country_iso3"]:
        frame[column] = frame[column].astype("string").str.strip()
        if frame[column].isna().any() or frame[column].eq("").any():
            raise ValueError(f"Missing key: {column}")
    if not frame["country_iso3"].str.fullmatch(r"[A-Z]{3}").all():
        raise ValueError("Country codes must be uppercase ISO3 codes")
    dates = pd.to_datetime(frame["date"], format="ISO8601", utc=True, errors="raise")
    if dates.isna().any() or not dates.eq(dates.dt.normalize()).all():
        raise ValueError("Dates must be known midnight UTC observations")
    frame["date"] = dates.dt.tz_localize(None)
    if frame.duplicated(["port_id", "date"]).any():
        raise ValueError("Duplicate (port_id,date): investigate rather than silently drop rows")
    if frame.groupby("port_id")["country_iso3"].nunique().gt(1).any():
        raise ValueError("A port_id maps to multiple countries")
    for column in ["import_tonnes", "export_tonnes", "portcalls"]:
        original = frame[column]
        frame[column] = pd.to_numeric(original, errors="coerce")
        if (original.notna() & frame[column].isna()).any():
            raise ValueError(f"Non-numeric measurement: {column}")
        known = frame[column].dropna()
        if known.lt(0).any() or not known.map(isfinite).all():
            raise ValueError(f"Negative or non-finite measurement: {column}")
    if frame["portcalls"].dropna().mod(1).ne(0).any():
        raise ValueError("Port calls must be whole nonnegative counts")
    # Use published import/export totals once; missing either makes cargo unknown.
    frame["cargo_tonnes"] = frame["import_tonnes"] + frame["export_tonnes"]
    if not frame["cargo_tonnes"].dropna().map(isfinite).all():
        raise ValueError("Non-finite derived cargo total")
    country_map = frame.groupby("port_id")["country_iso3"].first()
    calendar = pd.date_range(frame["date"].min(), frame["date"].max(), freq="D")
    index = pd.MultiIndex.from_product([sorted(country_map.index), calendar], names=["port_id", "date"])
    panel = frame.set_index(["port_id", "date"]).reindex(index).reset_index()
    panel["country_iso3"] = panel["port_id"].map(country_map)
    # Absent calendar rows retain missing measurements, never automatic zeros.
    return panel[PANEL_COLUMNS]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/ports_daily.csv"))
    args = parser.parse_args()
    if args.output.resolve().parent == args.input_dir.resolve():
        parser.error("Keep the cleaned output outside the raw input directory")
    try:
        raw = read_raw_files(args.input_dir)
        panel = clean_daily_panel(raw)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False, date_format="%Y-%m-%d", na_rep="", lineterminator="\n")
    print(f"Saved {len(panel):,} rows for {panel.port_id.nunique()} ports to {args.output}")
    print(f"Added missing calendar rows: {len(panel) - len(raw):,}; unknown cargo: {panel.cargo_tonnes.isna().sum():,}")
    print(f"Observed zero-cargo days preserved: {panel.cargo_tonnes.eq(0).sum():,}")


if __name__ == "__main__":
    main()
