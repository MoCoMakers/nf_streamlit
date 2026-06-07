#!/usr/bin/env python3
"""
Download public Google Drive dataset folders for the NCI-60 pipeline.

Default folder: MoCo Makers "Datasets" share
  https://drive.google.com/drive/folders/1e0_UQzU-LksJxMEN5zJRikL0QbsWrJej

Uses gdown (pip install gdown). Large folders may take a long time; use
--nci-only with a direct NCI subfolder ID to skip unrelated datasets.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import gdown
except ImportError as exc:
    print("ERROR: gdown is required. pip install gdown", file=sys.stderr)
    raise SystemExit(1) from exc

DEFAULT_DATASETS_ID = "1e0_UQzU-LksJxMEN5zJRikL0QbsWrJej"


def folder_url(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


def download_folder(folder_id: str, output_dir: Path, quiet: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    url = folder_url(folder_id)
    print(f"Downloading Drive folder {folder_id} -> {output_dir}")
    print(f"  URL: {url}")
    gdown.download_folder(
        url=url,
        output=str(output_dir),
        quiet=quiet,
        use_cookies=False,
        remaining_ok=True,
    )
    print("Download complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Datasets from Google Drive.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data"),
        help="Local directory (default: ./data)",
    )
    parser.add_argument(
        "--folder-id",
        default=os.environ.get("GDRIVE_DATASETS_FOLDER_ID", DEFAULT_DATASETS_ID),
        help="Google Drive folder ID (default: Datasets root or GDRIVE_DATASETS_FOLDER_ID)",
    )
    parser.add_argument(
        "--nci-only",
        action="store_true",
        help="Use GDRIVE_NCI_FOLDER_ID instead of full Datasets folder",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    folder_id = args.folder_id
    if args.nci_only:
        nci_id = os.environ.get("GDRIVE_NCI_FOLDER_ID")
        if not nci_id:
            print("ERROR: --nci-only requires GDRIVE_NCI_FOLDER_ID env var.", file=sys.stderr)
            raise SystemExit(1)
        folder_id = nci_id

    download_folder(folder_id, args.output.resolve(), quiet=args.quiet)


if __name__ == "__main__":
    main()
