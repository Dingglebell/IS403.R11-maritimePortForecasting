"""Download a separate, traceable HDX snapshot; never overwrite raw files.

This acquires country files only. It does not choose eligible ports, splits,
or modelling rules. Run from the repository root (Python standard library).
"""

import argparse
import csv
import gzip
import hashlib
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


COUNTRIES = (
    "indonesia", "philippines", "thailand", "singapore", "myanmar",
    "viet-nam", "malaysia", "cambodia", "brunei-darussalam", "timor-leste",
)
REQUIRED_FIELDS = {"date", "portid", "iso3", "import", "export", "portcalls"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def request(url, compress=False):
    headers = {"User-Agent": "IS403-Task1-data-access/1.0"}
    if compress:
        headers["Accept-Encoding"] = "gzip"
    return urlopen(Request(url, headers=headers), timeout=30)


def download_country(country, output_dir, resume=False):
    slug = f"{country}-daily-port-activity-data-and-shipment-estimates"
    api_url = f"https://data.humdata.org/api/3/action/package_show?id={slug}"
    with request(api_url) as response:
        package = json.load(response)
    if not package.get("success"):
        raise ValueError(f"HDX did not return a successful package: {slug}")
    metadata = package["result"]
    resources = [r for r in metadata["resources"] if r.get("format", "").upper() == "CSV"]
    if len(resources) != 1:
        raise ValueError(f"Expected exactly one CSV resource; found {len(resources)}")
    resource = resources[0]
    target = output_dir / f"{country}.csv"
    if target.exists() and not resume:
        raise FileExistsError(f"Raw file already exists; use a new snapshot directory: {target}")
    partial = target.with_suffix(".csv.part")
    if partial.exists() and not resume:
        raise FileExistsError(f"Incomplete file exists; inspect it before retrying: {partial}")
    expected_size = resource.get("size")
    (output_dir / f"{country}.metadata.json").write_text(
        json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    digest = hashlib.sha256()
    size = 0
    existing = target if target.exists() else partial
    reused = resume and existing.exists() and expected_size and existing.stat().st_size == expected_size
    final_url, content_type, last_modified, content_encoding = "", "", "", ""
    if reused:
        print(f"Verifying complete local download: {country}", flush=True)
    else:
        if target.exists():
            raise ValueError(f"Existing raw file size differs from current source metadata: {target}")
        if partial.exists():
            interrupted = partial.with_name(partial.name + f".interrupted-{time.time_ns()}")
            partial.rename(interrupted)
        started = time.monotonic()
        with request(resource["url"], compress=True) as response, partial.open("xb") as stream:
            final_url = response.url
            content_type = response.headers.get("Content-Type", "")
            last_modified = response.headers.get("Last-Modified", "")
            content_encoding = response.headers.get("Content-Encoding", "")
            reader = gzip.GzipFile(fileobj=response) if content_encoding.lower() == "gzip" else response
            print(f"Reading {country} ({content_type}; transfer={content_encoding or 'identity'})", flush=True)
            next_progress = 1024 * 1024
            for block in iter(lambda: reader.read1(64 * 1024), b""):
                stream.write(block)
                stream.flush()
                size += len(block)
                if size >= next_progress:
                    print(f"  {country}: {size:,} bytes received", flush=True)
                    next_progress = size + 5 * 1024 * 1024
                if time.monotonic() - started > 600:
                    raise TimeoutError(f"Download exceeded ten minutes after {size:,} bytes")
        existing = partial
    if expected_size and existing.stat().st_size != expected_size:
        raise ValueError(f"Incomplete CSV: {existing.stat().st_size} bytes; metadata declares {expected_size}")
    with existing.open(encoding="utf-8-sig", newline="") as stream:
        source_columns = next(csv.reader(stream))
    if not REQUIRED_FIELDS.issubset({name.casefold() for name in source_columns}):
        raise ValueError(f"Unexpected CSV header in {existing}; file left for inspection")
    with existing.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    size = existing.stat().st_size
    if existing != target:
        existing.rename(target)
    return {
        "file": target.as_posix(),
        "country": country,
        "source_url": f"https://data.humdata.org/dataset/{slug}",
        "metadata_url": api_url,
        "download_url": resource["url"],
        "resolved_download_url": final_url,
        "downloaded_at_utc": None if reused else utc_now(),
        "verified_at_utc": utc_now(),
        "local_file_mtime_utc": datetime.fromtimestamp(target.stat().st_mtime, timezone.utc).isoformat(),
        "sha256": digest.hexdigest(),
        "bytes": size,
        "content_type": content_type,
        "transfer_encoding": content_encoding,
        "source_columns": source_columns,
        "http_last_modified": last_modified,
        "source_metadata_modified": metadata.get("metadata_modified"),
        "source_resource_modified": resource.get("last_modified"),
        "source_declared_coverage": metadata.get("dataset_date"),
        "source_units": "estimated metric tonnes; port calls per day (HDX package notes)",
        "license_id": metadata.get("license_id"),
        "license_url": metadata.get("license_other"),
        "status": "downloaded_header_verified",
    }


def verify_snapshot(output_dir):
    """Check every byte against the manifest and inventory the original rows."""
    manifest_path = output_dir / "snapshot.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("errors") or not manifest.get("files"):
        raise ValueError("Snapshot has unresolved download failures or no files")
    inventory = []
    all_ports, all_keys = set(), set()
    for record in manifest["files"]:
        path = Path(record["file"])
        with path.open("rb") as stream:
            actual_hash = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual_hash != record["sha256"] or path.stat().st_size != record["bytes"]:
            raise ValueError(f"File changed since download: {path}")
        rows, duplicate_keys, missing_keys = 0, 0, 0
        ports, iso3s, dates = set(), set(), set()
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            columns = {column.casefold(): column for column in reader.fieldnames}
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f"Malformed CSV row {rows + 2}: {path}")
                rows += 1
                port_id = row[columns["portid"]]
                iso3 = row[columns["iso3"]]
                day = row[columns["date"]][:10]
                if not port_id or not iso3 or not day:
                    missing_keys += 1
                    continue
                date.fromisoformat(day)
                key = (port_id, day)
                duplicate_keys += key in all_keys
                all_keys.add(key)
                ports.add(port_id)
                iso3s.add(iso3)
                dates.add(day)
        all_ports.update(ports)
        inventory.append({
            "country": record["country"], "iso3": sorted(iso3s), "rows": rows,
            "ports": len(ports), "min_date": min(dates) if dates else None,
            "max_date": max(dates) if dates else None,
            "columns": len(columns), "duplicate_port_date_keys": duplicate_keys,
            "missing_keys": missing_keys, "sha256_verified": True,
        })
    result = {
        "checked_at_utc": utc_now(), "files": len(inventory),
        "rows": sum(row["rows"] for row in inventory), "ports": len(all_ports),
        "countries": inventory,
        "scope": "Original download inventory only; no cleaning, splitting or port selection",
    }
    (output_dir / "inventory.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


def export_manifest(output_dir, path):
    manifest = json.loads((output_dir / "snapshot.json").read_text(encoding="utf-8"))
    fields = [
        "file", "country", "source_url", "download_url", "downloaded_at_utc",
        "local_file_mtime_utc", "verified_at_utc", "sha256", "bytes",
        "source_units", "source_declared_coverage", "license_id", "license_url",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest["files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--countries", nargs="+", choices=COUNTRIES, default=list(COUNTRIES))
    parser.add_argument("--resume", action="store_true", help="Verify and reuse complete local downloads")
    parser.add_argument("--verify-only", action="store_true", help="Check hashes and inventory downloaded CSVs without network access")
    parser.add_argument("--manifest", type=Path, help="Export the provenance records as a local CSV")
    args = parser.parse_args()
    if args.verify_only:
        verify_snapshot(args.output_dir)
        if args.manifest:
            export_manifest(args.output_dir, args.manifest)
        return
    if len(set(args.countries)) != len(args.countries):
        parser.error("Do not repeat countries")
    manifest_path = args.output_dir / "snapshot.json"
    if manifest_path.exists() and not args.resume:
        parser.error("Snapshot already recorded; choose a new output directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at_utc": utc_now(),
        "source_family": "IMF PortWatch via HDX",
        "relation_to_group_snapshot": "new download; identity with the group snapshot is unverified",
        "study_scope_status": "acquisition only; final country/port scope is not agreed",
        "requested_countries": args.countries,
        "files": [],
        "errors": [],
    }
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["created_at_utc"] = previous["created_at_utc"]
        manifest["previous_attempt_errors"] = previous.get("previous_attempt_errors", []) + previous.get("errors", [])
        manifest["files"] = [r for r in previous["files"] if r["country"] not in args.countries]
    for country in args.countries:
        try:
            record = download_country(country, args.output_dir, args.resume)
            manifest["files"].append(record)
            print(f"Downloaded {country}: {record['bytes']:,} bytes", flush=True)
        except Exception as error:
            manifest["errors"].append({"country": country, "error": str(error)})
            print(f"FAILED {country}: {error}", flush=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if manifest["errors"]:
        raise SystemExit(1)
    if args.manifest:
        export_manifest(args.output_dir, args.manifest)
    print(f"Recorded {len(manifest['files'])} files in {manifest_path}")


if __name__ == "__main__":
    main()
