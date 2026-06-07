"""
One-shot pre-processor for data/NSC_Compounds/nsc_chemical_names.csv.

The source file contains 117 stray 0xbf bytes inside chemistry-name strings
where the upstream NCI export silently dropped two distinct Unicode characters:

    * Prime (U+2032 / apostrophe) -- positional indices and stereochem,
      e.g. [3',2':4,5] or 4,4'-DIHYDROXY
    * Right arrow (U+2192)        -- glycosidic linkages,
      e.g. (1->2), (1->4)

Heuristic substitution:

    digit (optional space) BF (optional space) digit  ->  RIGHT ARROW
    everything else                                  ->  APOSTROPHE

The cleaned file is written next to the source with .cleaned.csv suffix and is
valid UTF-8 so the standard csv_to_datawarehouse.py loader can ingest it.

Reference for chemistry truth is PubChem SID/CID (see raw_nci_nsc_sid_cid),
not these display names, so a small heuristic miss is acceptable.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path("data/NSC_Compounds/nsc_chemical_names.csv")
DST = Path("data/NSC_Compounds/nsc_chemical_names.cleaned.csv")

ARROW = "→"     # ->
PRIME = "'"           # plain ASCII apostrophe; simplest for downstream search

# digit (with optional whitespace) ¿ (with optional whitespace) digit  ->  arrow
ARROW_PATTERN = re.compile(r"(?<=\d)\s*¿\s*(?=\d)")


def clean(text: str) -> str:
    text = ARROW_PATTERN.sub(ARROW, text)
    text = text.replace("¿", PRIME)
    return text


def main() -> None:
    raw = SRC.read_bytes()
    bf_count = raw.count(b"\xbf")
    decoded = raw.decode("latin-1")
    cleaned = clean(decoded)
    DST.write_text(cleaned, encoding="utf-8")

    arrow_count = cleaned.count(ARROW)
    prime_count = bf_count - arrow_count  # bf's not turned into arrows became primes

    print(f"source     : {SRC} ({len(raw):,} bytes)")
    print(f"cleaned    : {DST} ({DST.stat().st_size:,} bytes)")
    print(f"0xbf bytes : {bf_count}")
    print(f"  -> arrow : {arrow_count}")
    print(f"  -> prime : {prime_count}")


if __name__ == "__main__":
    main()
