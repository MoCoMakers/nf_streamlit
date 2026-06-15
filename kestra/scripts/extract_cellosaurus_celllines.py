"""
Parse data/Cellosaurus/cellosaurus.txt and emit a flat CSV bridge between
the Cellosaurus primary ID (CVCL_xxxx), the cell line name, synonyms, and
the two cross-reference IDs we care about for joining NCI-60 dose-response
data to DepMap:

    cvcl_id        Cellosaurus primary accession (AC line)
    name           Display name (ID line)
    synonyms       Synonyms from SY line, pipe-delimited, NULL if absent
    depmap_ach     'DR DepMap; ACH-#######' values, pipe-delimited
    nci_dtp_name   'DR NCI-DTP; <name>' values, pipe-delimited

Why no NSC column: NSC numbers identify compounds, not cell lines. The
NCI-60 panel addresses cell lines by NCI-DTP names (A549, MCF7, ...), which
Cellosaurus carries on its DR NCI-DTP lines.

List delimiter is the pipe character ('|') because ~2,500 Cellosaurus
cell-line names/synonyms already contain commas (e.g. '207,B-4',
'2C4 [Mouse hybridoma against 2,4-D/2,4-DP]'). If any name or synonym
already contains a pipe the script aborts so the operator can pick a
different scheme — a silent escape would be worse than a loud failure.

Reads:   data/Cellosaurus/cellosaurus.txt
Writes:  data/Cellosaurus/cellosaurus_celllines.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

DEFAULT_SRC = Path("data/Cellosaurus/cellosaurus.txt")
DEFAULT_DST = Path("data/Cellosaurus/cellosaurus_celllines.csv")

HEADERS = ["cvcl_id", "name", "synonyms", "depmap_ach", "nci_dtp_name"]


def parse_entries(path: Path):
    """Yield one dict per cellosaurus entry."""
    cur: dict | None = None
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line == "//":
                if cur is not None:
                    yield cur
                cur = None
                continue
            if len(line) < 5 or line[2:5] != "   ":
                # Header / blank / comment outside an entry.
                continue
            code = line[:2]
            value = line[5:]
            if code == "ID":
                cur = {"name": value, "cvcl_id": None,
                       "synonyms": [], "depmap_ach": [], "nci_dtp_name": []}
            elif cur is None:
                continue
            elif code == "AC":
                cur["cvcl_id"] = value
            elif code == "SY":
                # SY line is "; " separated.
                cur["synonyms"] = [s.strip() for s in value.split(";") if s.strip()]
            elif code == "DR":
                # 'DR   <db>; <id>'
                if ";" not in value:
                    continue
                db, ident = value.split(";", 1)
                db = db.strip()
                ident = ident.strip()
                if db == "DepMap":
                    cur["depmap_ach"].append(ident)
                elif db == "NCI-DTP":
                    cur["nci_dtp_name"].append(ident)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse Cellosaurus flat file into a flat cell-line/xref CSV."
    )
    parser.add_argument(
        "--src", type=Path, default=DEFAULT_SRC,
        help=f"Cellosaurus flat file (default: {DEFAULT_SRC})",
    )
    parser.add_argument(
        "--dst", type=Path, default=DEFAULT_DST,
        help=f"Output CSV (default: {DEFAULT_DST})",
    )
    parser.add_argument(
        "--skip-if-exists", action="store_true",
        help="No-op if the output CSV already exists (idempotent pipeline reruns).",
    )
    args = parser.parse_args()
    SRC, DST = args.src, args.dst

    if args.skip_if_exists and DST.exists():
        print(f"Output already present, skipping extract: {DST}")
        return 0
    if not SRC.exists():
        print(f"ERROR: source file not found: {SRC}", file=sys.stderr)
        return 1

    DELIM = "|"
    pipe_offenders: list[tuple[str, str, str]] = []
    rows: list[dict] = []

    for entry in parse_entries(SRC):
        name = entry["name"]
        if DELIM in name:
            pipe_offenders.append((entry["cvcl_id"] or "?", "name", name))
        for syn in entry["synonyms"]:
            if DELIM in syn:
                pipe_offenders.append((entry["cvcl_id"] or "?", "synonym", syn))

        rows.append({
            "cvcl_id":      entry["cvcl_id"] or "",
            "name":         name,
            "synonyms":     DELIM.join(entry["synonyms"]) if entry["synonyms"] else "",
            "depmap_ach":   DELIM.join(entry["depmap_ach"]) if entry["depmap_ach"] else "",
            "nci_dtp_name": DELIM.join(entry["nci_dtp_name"]) if entry["nci_dtp_name"] else "",
        })

    if pipe_offenders:
        print(
            f"ABORT: {len(pipe_offenders)} cell-line name/synonym entries "
            f"contain the chosen pipe delimiter '{DELIM}'. Examples:",
            file=sys.stderr,
        )
        for cvcl, kind, val in pipe_offenders[:20]:
            print(f"  {cvcl}  ({kind}) -> {val!r}", file=sys.stderr)
        if len(pipe_offenders) > 20:
            print(f"  ... and {len(pipe_offenders) - 20} more", file=sys.stderr)
        return 2

    with DST.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"entries parsed   : {len(rows):,}")
    print(f"  with DepMap    : {sum(1 for r in rows if r['depmap_ach']):,}")
    print(f"  with NCI-DTP   : {sum(1 for r in rows if r['nci_dtp_name']):,}")
    print(f"  with synonyms  : {sum(1 for r in rows if r['synonyms']):,}")
    print(f"output           : {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
