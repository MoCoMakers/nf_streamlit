#!/usr/bin/env python3
"""
Orchestrate NCI-60 raw CSV download (Google Drive) + PostgreSQL bulk load.

Designed for Kestra (PG* env vars) and local runs (--config scripts/config.yaml).

  python kestra/scripts/load_nci60_raw.py
  python kestra/scripts/load_nci60_raw.py --only doseresp          # local-first; downloads if missing
  python kestra/scripts/load_nci60_raw.py --skip-download          # never download (fail if missing)
  python kestra/scripts/load_nci60_raw.py --force-download         # always re-fetch from Drive
  python kestra/scripts/load_nci60_raw.py --dry-run

csv_to_datawarehouse.py lives alongside this script in kestra/scripts/.
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


def _import_loader(repo_root: Path):
    scripts_dir = str(Path(__file__).resolve().parent)
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

    cmd = [sys.executable, str(Path(__file__).resolve().parent / "clean_nsc_chemical_names.py")]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("clean_nsc_chemical_names.py failed")
    if cleaned.exists():
        return cleaned
    raise FileNotFoundError(f"Expected cleaned CSV at {cleaned}")


def _env_bool(name: str) -> bool | None:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip().lower() in ("1", "true", "yes")


def missing_local_csvs(
    data_root: Path, loads: list[dict], path_variant: str | None
) -> list[str]:
    """Manifest entry ids with no resolvable CSV under data_root."""
    missing: list[str] = []
    for entry in loads:
        path = resolve_csv_path(data_root, entry, path_variant)
        if not path.exists():
            missing.append(entry["id"])
    return missing


def should_download(
    *,
    data_root: Path,
    loads: list[dict],
    path_variant: str | None,
    skip_download: bool,
    force_download: bool,
    dry_run: bool,
) -> tuple[bool, list[str]]:
    """Local-first: download only when CSVs are missing unless forced or skipped."""
    if skip_download and force_download:
        raise SystemExit("ERROR: --skip-download and --force-download are mutually exclusive.")

    if skip_download:
        missing = missing_local_csvs(data_root, loads, path_variant)
        if missing:
            print(
                f"SKIP_DOWNLOAD set; missing local CSVs for: {', '.join(missing)}",
                file=sys.stderr,
            )
        return False, missing

    if force_download:
        print(f"FORCE_DOWNLOAD: re-fetching from Drive into {data_root}")
        return True, []

    missing = missing_local_csvs(data_root, loads, path_variant)
    if not missing:
        print(f"Local data present under {data_root}; skipping Drive download.")
        return False, []
    print(f"Missing local CSVs ({', '.join(missing)}); downloading from Drive.")
    return True, missing


def run_download(manifest: dict, data_root: Path, nci_only: bool, repo_root: Path) -> None:
    drive = manifest.get("drive") or {}
    folder_id = drive.get("datasets_folder_id")
    if nci_only and drive.get("nci_only_folder_id"):
        folder_id = drive["nci_only_folder_id"]

    cmd = [
        sys.executable,
        str(repo_root / "kestra" / "scripts" / "download_gdrive_datasets.py"),
        "--output",
        str(data_root),
        "--folder-id",
        str(folder_id),
    ]
    if nci_only:
        cmd.append("--nci-only")
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=repo_root, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download + load NCI-60 raw CSVs.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--config", help="YAML config (optional if PG* env set)")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="CSV tree root (default: {repo}/data). Use a host path e.g. /tmp/kestra-wd/nf-datasets to persist across runs.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Never download; fail at load if local CSVs are missing.",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Always download from Drive, even when local CSVs exist.",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download to data-root and exit (no PostgreSQL load).",
    )
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
    repo_root = args.repo_root.resolve()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    if args.data_root is not None:
        data_root = args.data_root.resolve()
    elif os.environ.get("DATA_ROOT"):
        data_root = Path(os.environ["DATA_ROOT"]).resolve()
    else:
        data_root = (repo_root / manifest.get("data_root", "data")).resolve()
    loads = manifest.get("loads") or []
    only_ids = list(args.only or [])
    if os.environ.get("ONLY_TABLES"):
        only_ids.extend(x.strip() for x in os.environ["ONLY_TABLES"].split(",") if x.strip())
    if only_ids:
        allowed = set(only_ids)
        loads = [e for e in loads if e["id"] in allowed]

    skip_download = args.skip_download or _env_bool("SKIP_DOWNLOAD") is True
    force_download = args.force_download or _env_bool("FORCE_DOWNLOAD") is True

    do_download, missing = should_download(
        data_root=data_root,
        loads=loads,
        path_variant=args.path_variant,
        skip_download=skip_download,
        force_download=force_download,
        dry_run=args.dry_run,
    )

    if do_download:
        if args.dry_run:
            print(f"DRY RUN: would download to {data_root}")
        else:
            run_download(manifest, data_root, args.nci_only, repo_root)
    elif missing and skip_download:
        raise SystemExit(1)

    if args.download_only:
        if do_download and not args.dry_run:
            print(f"Download-only complete. CSVs under {data_root}")
        elif not do_download:
            print(f"Download-only: local cache sufficient under {data_root}")
        return

    load_config_fn, load_csv_fn = _import_loader(repo_root)
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
            csv_path = preprocess_clean_names(repo_root, csv_path)

        if args.dry_run:
            print(f"DRY RUN: would load into {table} replace={replace}")
            continue

        load_csv_fn(str(csv_path), table, config, replace=replace)

    print("\nAll requested loads finished.")


if __name__ == "__main__":
    main()
