"""
Build a Cellosaurus <-> NCI-60 cell-line bridge CSV.

Reads Cellosaurus flat file, indexes every entry by its primary ID and all synonyms
(normalized), then matches the distinct NCI-60 cell_name values against that index.

Output CSV (one row per NCI-60 cell_name) -> loaded as raw_cellosaurus_nci60_bridge:
    nci60_cell_name      original NCI-60 name
    matched_on           how matched: 'primary' | 'synonym' | 'unmatched'
    cvcl                 Cellosaurus accession(s), pipe-delimited if >1 entry matched
    cellosaurus_name     Cellosaurus primary ID(s), pipe-delimited
    ach                  DepMap ACH code(s), pipe-delimited; empty if none
    n_ach                count of ACH codes
    synonyms             Cellosaurus synonyms of matched entry/entries, pipe-delimited

Delimiter is the PIPE character '|' (per request) because cell names contain commas
and slashes. NCI-60 names are read live from the DB via the MCP toolbox is NOT used here;
instead the caller passes them in, or we hardcode from a query dump.
"""
import csv
import re
import sys
from pathlib import Path

CELL_TXT = Path("data/Cellosaurus/cellosaurus.txt")
OUT = Path("data/Cellosaurus/raw_cellosaurus_nci60_bridge.csv")
PIPE = "|"


def norm(name: str) -> str:
    """Uppercase, drop all non-alphanumerics -> 'A549/ATCC' == 'A-549' base differs, handled by suffix pass."""
    return re.sub(r"[^0-9A-Z]+", "", name.upper())


def parse_cellosaurus(path: Path):
    """Yield dict per entry: cvcl, name, synonyms(list), ach(list), taxid."""
    cur = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            code = line[:2]
            if code == "ID":
                cur = {"name": line[5:].rstrip("\n").strip(), "cvcl": None,
                        "syn": [], "ach": [], "taxid": None}
            elif cur is None:
                continue
            elif code == "AC" and cur["cvcl"] is None:
                cur["cvcl"] = line[5:].strip()
            elif code == "SY":
                cur["syn"] = [s.strip() for s in line[5:].strip().split(";") if s.strip()]
            elif code == "DR":
                body = line[5:].strip()
                if body.startswith("DepMap;"):
                    cur["ach"].append(body.split(";", 1)[1].strip())
            elif code == "OX" and cur["taxid"] is None:
                m = re.search(r"NCBI_TaxID=(\d+)", line)
                if m:
                    cur["taxid"] = m.group(1)
            elif line.startswith("//"):
                if cur["cvcl"]:
                    yield cur
                cur = None


def build_index(entries):
    """normalized name -> list of entry refs. Prefer human + ACH-bearing on collisions."""
    idx = {}
    for e in entries:
        keys = {norm(e["name"])} | {norm(s) for s in e["syn"]}
        for k in keys:
            if k:
                idx.setdefault(k, []).append(e)
    return idx


def pick(entries):
    """Among entries sharing a normalized name, prefer human (9606) ones with ACH."""
    human = [e for e in entries if e["taxid"] == "9606"]
    pool = human or entries
    with_ach = [e for e in pool if e["ach"]]
    return with_ach or pool


def match(nci_name, idx):
    candidates = [norm(nci_name)]
    # suffix pass: NCI-60 uses '/ATCC', '/H.Fine', clone tags. Try base before first '/'.
    if "/" in nci_name:
        candidates.append(norm(nci_name.split("/")[0]))
    for i, key in enumerate(candidates):
        if key in idx:
            return ("primary" if i == 0 else "synonym"), pick(idx[key])
    return "unmatched", []


def main():
    # NCI-60 names: from a --names-file (one per line) or as positional args.
    nci_names = []
    args = sys.argv[1:]
    if args and args[0] == "--names-file":
        nci_names = [ln.strip() for ln in Path(args[1]).read_text(encoding="utf-8").splitlines()
                     if ln.strip()]
    else:
        nci_names = [a for a in args]
    if not nci_names:
        print("ERROR: pass --names-file PATH or NCI-60 cell names as args", file=sys.stderr)
        sys.exit(1)

    entries = list(parse_cellosaurus(CELL_TXT))
    idx = build_index(entries)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nci60_cell_name", "matched_on", "cvcl", "cellosaurus_name",
                    "ach", "n_ach", "synonyms"])
        for name in nci_names:
            how, hits = match(name, idx)
            cvcl = PIPE.join(e["cvcl"] for e in hits)
            cname = PIPE.join(e["name"] for e in hits)
            achs = [a for e in hits for a in e["ach"]]
            ach = PIPE.join(achs)
            syns = PIPE.join(s for e in hits for s in e["syn"])
            w.writerow([name, how, cvcl, cname, ach, len(achs), syns])

    print(f"Wrote {OUT} for {len(nci_names)} NCI-60 names "
          f"({len(entries)} Cellosaurus entries indexed).")


if __name__ == "__main__":
    main()
