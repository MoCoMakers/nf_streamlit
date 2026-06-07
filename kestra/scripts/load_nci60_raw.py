#!/usr/bin/env python3
"""
Orchestrate NCI-60 raw CSV download (Google Drive) + PostgreSQL bulk load.

Designed for Kestra (PG* env vars) and local runs (--config scripts/config.yaml).

  python kestra/scripts/load_nci60_raw.py
  python kestra/scripts/load_nci60_raw.py --skip-download --only doseresp
  python kestra/scripts/load_nci60_raw.py --dry-run

Requires repo root as cwd (or pass --repo-root) so scripts/csv_to_datawarehouse.py
is importable.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DEFAULT = Path(__file__).resolve().parent / "nci60_manifest.yaml"


def _import_loader():
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from csv_to_datawarehouse import load_config, load_csv  # noqa: WPS433

    return load_config, load_csv


def resolve_csv_path(data_root: Path, entry: dict, path_variant: str | None) -> Path:
    rel = entry["relative_path"]
    if path_variant and path_variant in (entry.get("path_variants") or {}):
        rel = entry["path_variants"][path_variant]
    path = data_root / rel
    if path.exists():
        return path
    # Try basename search under data_root (Drive layout drift)
    matches = list(data_root.rglob(Path(rel).name))
    if len(matches) == 1:
        print(f"  Resolved {rel} -> {matches[0]}")
        return matches[0]
    if len(matches) > 1:
        print(f"  WARNING: multiple matches for {Path(rel).name}; using first: {matches[0]}")
        return matches[0]
    return path


def preprocess_clean_names(repo_root: Path, csv_path: Path) -> Path:
    """Run clean_nsc_chemical_names; return path to cleaned CSV."""
    nsc_dir = repo_root / "data" / "NSC_Compounds"
    nsc_dir.mkdir(parents=True, exist_ok=True)
    target_src = nsc_dir / csv_path.name
    if csv_path.resolve() != target_src.resolve():
        import shutil

        shutil.copy2(csv_path, target_src)
        csv_path = target_src

    cleaned = nsc_dir / "nsc_chemical_names.cleaned.csv"
    if cleaned.exists() and cleaned.stat().st_mtime >= csv_path.stat().st_mtime:
        print(f"  Using existing cleaned file: {cleaned}")
        return cleaned

    cmd = [sys.executable, str(repo_root / "scripts" / "clean_nsc_chemical_names.py")]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("clean_nsc_chemical_names.py failed")
    if cleaned.exists():
        return cleaned
    raise FileNotFoundError(f"Expected cleaned CSV at {cleaned}")


def run_download(manifest: dict, data_root: Path, nci_only: bool) -> None:
    drive = manifest.get("drive") or {}
    folder_id = drive.get("datasets_folder_id")
    if nci_only and drive.get("nci_only_folder_id"):
        folder_id = drive["nci_only_folder_id"]

    cmd = [
        sys.executable,
        str(REPO_ROOT / "kestra" / "scripts" / "download_gdrive_datasets.py"),
        "--output",
        str(data_root),
        "--folder-id",
        str(folder_id),
    ]
    if nci_only:
        cmd.append("--nci-only")
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download + load NCI-60 raw CSVs.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--config", help="YAML config (optional if PG* env set)")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--nci-only", action="store_true", help="Download NCI subfolder only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        metavar="ID",
        help="Load subset by manifest id (e.g. doseresp, nsc_cas). Repeatable.",
    )
    parser.add_argument("--path-variant", choices=["flat_nci60", "flat_nsc"], default=None)
    args = parser.parse_args()

    global REPO_ROOT
    REPO_ROOT = args.repo_root.resolve()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    data_root = REPO_ROOT / manifest.get("data_root", "data")
    loads = manifest.get("loads") or []
    only_ids = list(args.only or [])
    if os.environ.get("ONLY_TABLES"):
        only_ids.extend(x.strip() for x in os.environ["ONLY_TABLES"].split(",") if x.strip())
    if only_ids:
        allowed = set(only_ids)
        loads = [e for e in loads if e["id"] in allowed]

    if not args.skip_download:
        if args.dry_run:
            print(f"DRY RUN: would download to {data_root}")
        else:
            run_download(manifest, data_root, args.nci_only)

    load_config_fn, load_csv_fn = _import_loader()
    config = load_config_fn(args.config)

    for entry in loads:
        eid = entry["id"]
        csv_path = resolve_csv_path(data_root, entry, args.path_variant)
        table = entry["table"]
        replace = entry.get("replace", True)

        print(f"\n=== [{eid}] {table} <= {csv_path} ===")
        if not csv_path.exists():
            msg = f"CSV not found: {csv_path}"
            if entry.get("required"):
                print(f"ERROR: {msg}", file=sys.stderr)
                raise SystemExit(1)
            print(f"SKIP (optional): {msg}")
            continue

        if entry.get("preprocess") == "clean_nsc_chemical_names":
            csv_path = preprocess_clean_names(REPO_ROOT, csv_path)

        if args.dry_run:
            print(f"DRY RUN: would load into {table} replace={replace}")
            continue

        load_csv_fn(str(csv_path), table, config, replace=replace)

    print("\nAll requested loads finished.")


if __name__ == "__main__":
    main()
