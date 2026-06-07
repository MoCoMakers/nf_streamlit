#!/usr/bin/env python3
"""
pubchem_enrich.py
=================
Enriches im_nci_nci60_doseresp_sprime_list with compound metadata by
querying the PubChem PUG REST API and joining to our local ChEMBL 37 database.

Columns populated
-----------------
  common_name           PubChem preferred title  (e.g. "Doxorubicin")
  chembl_id             ChEMBL compound ID        (e.g. "CHEMBL53463")
  chembl_compound_name  ChEMBL preferred name
  chembl_moa            Mechanism(s) of action, semicolon-joined
  chembl_compound_class ATC level-4 drug class,  semicolon-joined

Join path
---------
  im_nci_nsc_compounds.pubchem_cid
    → PubChem REST /compound/cid/{cids}/property/Title,InChIKey/JSON
        → Title          → common_name
        → InChIKey       → chembl.compound_structures.standard_inchi_key
                             → chembl_id, chembl_compound_name
                             → chembl.drug_mechanism (via molecule_hierarchy)
                             → chembl.atc_classification

Coverage
--------
  96.5 % of distinct NSCs in the sprime list have a pubchem_cid.
  ChEMBL MOA / class data is available only for curated drugs (~7 500 compounds).

Rate limiting
-------------
  PubChem enforces:  ≤ 5 requests / second, ≤ 400 requests / minute.
  Violation can result in a temporary IP block from all NCBI services.

  This script reads the X-Throttling-Control header on every response and
  adjusts its sleep interval dynamically:
    Green  (< 40 %)  → 0.21 s between batches  (~4.7 req/sec, safe margin)
    Yellow (40-70 %)  → 0.5  s                  (~2   req/sec)
    Red    (> 70 %)   → 2.0  s + jitter          (~0.5 req/sec)
  HTTP 429 / 503     → exponential backoff, up to MAX_RETRIES attempts.

Usage
-----
  # Inside Docker (recommended — all deps present):
  docker compose -f infra/docker-compose.yml --profile tools run --rm tools \\
      python scripts/pubchem_enrich.py

  # Locally:
  pip install "psycopg[binary]" pyyaml requests tqdm
  python scripts/pubchem_enrich.py [--config scripts/config.yaml]

  # Flags:
  --config PATH        Path to DB config YAML  (default: scripts/config.yaml)
  --batch-size N       CIDs per PubChem request (default: 100, max ~100)
  --flush-every N      Write to DB after every N batches (default: 50)
  --overwrite          Re-fetch and overwrite existing common_name values
  --dry-run            Fetch from PubChem but do not write to the database
"""

import argparse
import logging
import random
import re
import time
from typing import Iterator

import psycopg
import requests
import yaml
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PUBCHEM_PROPERTY_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    "/compound/cid/{cids}/property/Title,InChIKey/JSON"
)

# Baseline sleep between requests (seconds).  Keeps us well below 5 req/sec.
SLEEP_GREEN  = 0.21
SLEEP_YELLOW = 0.50
SLEEP_RED    = 2.00

MAX_RETRIES    = 5
BACKOFF_BASE   = 2.0   # seconds; doubled on each retry

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration / database
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return cfg["database"]


def get_conn(cfg: dict):
    return psycopg.connect(
        host=cfg["host"],
        port=cfg.get("port", 5432),
        dbname=cfg["name"],
        user=cfg["user"],
        password=cfg["password"],
    )


# ---------------------------------------------------------------------------
# Work-item enumeration
# ---------------------------------------------------------------------------

def get_work_items(conn, overwrite: bool) -> list[tuple[str, str]]:
    """
    Return [(nsc, pubchem_cid), ...] for compounds that need enrichment.

    Without --overwrite, skips rows where common_name is already populated
    (preserves prior PubChem runs; does not skip ChEMBL-only rows from
    the NSC-code Tier-1 update, since those used a different path).
    """
    filter_clause = "" if overwrite else "AND s.common_name IS NULL"
    sql = f"""
        SELECT DISTINCT s.nsc, c.pubchem_cid
        FROM im_nci_nci60_doseresp_sprime_list s
        JOIN im_nci_nsc_compounds c ON c.nsc = s.nsc
        WHERE c.pubchem_cid IS NOT NULL
          {filter_clause}
        ORDER BY s.nsc
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def batched(items: list, n: int) -> Iterator[list]:
    """Yield successive n-sized chunks from items."""
    for i in range(0, len(items), n):
        yield items[i : i + n]


# ---------------------------------------------------------------------------
# PubChem API — throttle-aware
# ---------------------------------------------------------------------------

def _parse_throttle_header(response: requests.Response) -> dict:
    """
    Parse the X-Throttling-Control header into a dict with keys:
      request_count_pct, request_time_pct, service_pct, worst_pct, status

    Header format (example):
      Request Count status: Green (12%), Request Time status: Yellow (45%),
      Service status: Green (3%)
    """
    header = response.headers.get("X-Throttling-Control", "")
    pcts = [int(m) for m in re.findall(r"\((\d+)%\)", header)]
    worst = max(pcts) if pcts else 0

    if worst < 40:
        status = "Green"
    elif worst < 70:
        status = "Yellow"
    else:
        status = "Red"

    return {"worst_pct": worst, "status": status, "raw": header}


def _sleep_for_throttle(throttle: dict) -> float:
    """Sleep an appropriate amount based on throttle status; return sleep duration."""
    status = throttle.get("status", "Green")
    if status == "Red":
        secs = SLEEP_RED + random.uniform(0, 0.5)   # jitter avoids synchronized bursts
    elif status == "Yellow":
        secs = SLEEP_YELLOW
    else:
        secs = SLEEP_GREEN
    time.sleep(secs)
    return secs


def fetch_pubchem_batch(
    cid_list: list[str],
    session: requests.Session,
) -> tuple[dict, dict]:
    """
    Query PubChem for a batch of CIDs.

    Returns:
      results  : {cid_str: {"title": str, "inchikey": str}}
      throttle : parsed throttle dict from the last response
    """
    cids_param = ",".join(cid_list)
    url = PUBCHEM_PROPERTY_URL.format(cids=cids_param)

    throttle = {"status": "Green", "worst_pct": 0, "raw": ""}
    delay = BACKOFF_BASE

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=30)
            throttle = _parse_throttle_header(resp)

            if resp.status_code == 200:
                data = resp.json()
                props = data.get("PropertyTable", {}).get("Properties", [])
                results = {
                    str(p["CID"]): {
                        "title":    p.get("Title", ""),
                        "inchikey": p.get("InChIKey", ""),
                    }
                    for p in props
                }
                return results, throttle

            elif resp.status_code in (429, 503):
                log.warning(
                    "HTTP %d on attempt %d/%d — backing off %.1fs",
                    resp.status_code, attempt, MAX_RETRIES, delay,
                )
                time.sleep(delay)
                delay *= 2
                continue

            else:
                log.error("Unexpected HTTP %d for CIDs %s", resp.status_code, cids_param[:80])
                return {}, throttle

        except requests.RequestException as exc:
            log.warning("Request error on attempt %d/%d: %s", attempt, MAX_RETRIES, exc)
            time.sleep(delay)
            delay *= 2

    log.error("All %d retries exhausted for batch starting at CID %s", MAX_RETRIES, cid_list[0])
    return {}, throttle


# ---------------------------------------------------------------------------
# Database writes
# ---------------------------------------------------------------------------

# SQL template for flushing a batch of (nsc, title, inchikey) rows.
# {placeholders} is replaced at runtime with the correct number of (%s,%s,%s) tuples.
#
# Strategy:
#   - common_name       : always overwrite — PubChem Title is authoritative
#   - chembl_*          : COALESCE preserves existing Tier-1 NSC-code matches,
#                         fills NULLs via InChIKey → ChEMBL join

_FLUSH_SQL_TEMPLATE = """
WITH incoming (nsc, pubchem_title, inchikey) AS (
    VALUES {placeholders}
),
moa_by_parent AS (
    SELECT
        mh1.parent_molregno,
        string_agg(
            DISTINCT dm.mechanism_of_action, '; '
            ORDER BY dm.mechanism_of_action
        ) AS moa_text
    FROM chembl.molecule_hierarchy mh1
    JOIN chembl.molecule_hierarchy mh2
        ON mh2.parent_molregno = mh1.parent_molregno
    JOIN chembl.drug_mechanism dm ON dm.molregno = mh2.molregno
    GROUP BY mh1.parent_molregno
),
atc_by_molregno AS (
    SELECT
        mac.molregno,
        string_agg(
            DISTINCT ac.level4_description, '; '
            ORDER BY ac.level4_description
        ) AS compound_class
    FROM chembl.molecule_atc_classification mac
    JOIN chembl.atc_classification ac ON ac.level5 = mac.level5
    GROUP BY mac.molregno
),
chembl_enriched AS (
    SELECT DISTINCT ON (i.nsc)
        i.nsc,
        i.pubchem_title,
        md.chembl_id,
        md.pref_name         AS chembl_name,
        moa.moa_text,
        atc.compound_class
    FROM incoming i
    LEFT JOIN chembl.compound_structures cs
        ON cs.standard_inchi_key = i.inchikey AND i.inchikey <> ''
    LEFT JOIN chembl.molecule_dictionary md
        ON md.molregno = cs.molregno
    LEFT JOIN moa_by_parent moa
        ON moa.parent_molregno = md.molregno
    LEFT JOIN atc_by_molregno atc
        ON atc.molregno = md.molregno
)
UPDATE im_nci_nci60_doseresp_sprime_list s
SET
    common_name           = ce.pubchem_title,
    chembl_id             = COALESCE(s.chembl_id,             ce.chembl_id),
    chembl_compound_name  = COALESCE(s.chembl_compound_name,  ce.chembl_name),
    chembl_moa            = COALESCE(s.chembl_moa,            ce.moa_text),
    chembl_compound_class = COALESCE(s.chembl_compound_class, ce.compound_class)
FROM chembl_enriched ce
WHERE ce.nsc = s.nsc
"""


def flush_to_db(conn, records: list[tuple[str, str, str]], dry_run: bool) -> int:
    """
    Write a list of (nsc, pubchem_title, inchikey) records to the database.
    Builds the VALUES clause with explicit %s placeholders (psycopg3 compatible).
    Returns the number of rows updated.
    """
    if not records:
        return 0
    if dry_run:
        log.debug("dry-run: would flush %d records", len(records))
        return 0

    placeholders = ", ".join(["(%s, %s, %s)"] * len(records))
    sql = _FLUSH_SQL_TEMPLATE.format(placeholders=placeholders)
    params = [val for row in records for val in row]

    with conn.cursor() as cur:
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Enrich sprime list with PubChem titles and ChEMBL annotations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--config",      default="scripts/config.yaml",
                        help="Path to DB config YAML")
    parser.add_argument("--batch-size",  type=int, default=100,
                        help="CIDs per PubChem request (max ~100)")
    parser.add_argument("--flush-every", type=int, default=50,
                        help="Write to DB after every N batches")
    parser.add_argument("--overwrite",   action="store_true",
                        help="Re-fetch and overwrite existing common_name values")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Fetch from PubChem but skip all DB writes")
    args = parser.parse_args()

    cfg  = load_config(args.config)
    conn = get_conn(cfg)

    # ---- Ensure columns exist ------------------------------------------------
    with conn.cursor() as cur:
        for col, typ in [
            ("common_name",           "text"),
            ("chembl_id",             "text"),
            ("chembl_compound_name",  "text"),
            ("chembl_moa",            "text"),
            ("chembl_compound_class", "text"),
        ]:
            cur.execute(f"""
                ALTER TABLE im_nci_nci60_doseresp_sprime_list
                ADD COLUMN IF NOT EXISTS {col} {typ}
            """)
    conn.commit()

    # ---- Load work items -----------------------------------------------------
    log.info("Querying work items from database …")
    work = get_work_items(conn, args.overwrite)
    log.info("%d distinct (NSC, CID) pairs to process", len(work))
    if not work:
        log.info("Nothing to do — use --overwrite to re-process existing rows.")
        return

    # Build nsc→cid and cid→[nsc] maps
    cid_to_nscs: dict[str, list[str]] = {}
    for nsc, cid in work:
        cid_to_nscs.setdefault(cid, []).append(nsc)

    unique_cids = list(cid_to_nscs.keys())
    total_batches = (len(unique_cids) + args.batch_size - 1) // args.batch_size
    log.info("%d unique CIDs → %d batches of %d", len(unique_cids), total_batches, args.batch_size)

    # ---- Main loop -----------------------------------------------------------
    session = requests.Session()
    session.headers.update({"User-Agent": "nf_streamlit_enrich/1.0 (gotimlabs@gmail.com)"})

    pending:        list[tuple[str, str, str]] = []   # (nsc, title, inchikey)
    total_updated   = 0
    total_fetched   = 0
    throttle_status = "Green"

    pbar = tqdm(
        total=total_batches,
        unit="batch",
        desc="PubChem",
        dynamic_ncols=True,
    )

    for batch_idx, cid_batch in enumerate(batched(unique_cids, args.batch_size), start=1):
        results, throttle = fetch_pubchem_batch(cid_batch, session)
        throttle_status   = throttle["status"]
        total_fetched    += len(results)

        # Map results back to NSCs
        for cid, props in results.items():
            title    = props.get("title", "") or ""
            inchikey = props.get("inchikey", "") or ""
            for nsc in cid_to_nscs.get(cid, []):
                pending.append((nsc, title, inchikey))

        # Flush to DB every flush_every batches or on the last batch
        is_last = batch_idx == total_batches
        if len(pending) > 0 and (batch_idx % args.flush_every == 0 or is_last):
            n = flush_to_db(conn, pending, args.dry_run)
            total_updated += n
            pending.clear()

        pbar.set_postfix({
            "throttle":  f"{throttle_status} {throttle['worst_pct']}%",
            "fetched":   total_fetched,
            "db_rows":   total_updated,
        })
        pbar.update(1)

        _sleep_for_throttle(throttle)

    pbar.close()
    session.close()
    conn.close()

    log.info("Done. PubChem records fetched: %d  |  DB rows updated: %d",
             total_fetched, total_updated)

    if args.dry_run:
        log.info("(dry-run mode — no changes written to the database)")


if __name__ == "__main__":
    main()
