#!/usr/bin/env python3
"""
enrich_chembl_compounds.py
==========================
Populates chembl_id, chembl_compound_name, chembl_moa, and chembl_compound_class
on im_nci_nci60_doseresp_sprime_list by joining NCI compounds to our local
ChEMBL 37 database (loaded as the 'chembl' foreign schema in data_warehouse).

Join strategy (three tiers, applied in order of reliability):

  Tier 1 – NSC research code  (SQL-only, ~945 compounds)
    molecule_synonyms WHERE syn_type='RESEARCH_CODE' AND synonyms='NSC-<nsc>'

  Tier 2 – InChIKey from SMILES via RDKit  (~80 %+ coverage)
    Compute standard InChIKey from the SMILES in im_nci_nsc_compounds,
    then join to chembl.compound_structures.standard_inchi_key.
    Requires: pip install rdkit  (or conda install -c conda-forge rdkit)

  Tier 3 – PubChem CID → InChIKey via FTP bulk file  (fallback when RDKit absent)
    Downloads ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-InChI-Key.gz
    (~600 MB, cached locally), maps pubchem_cid → InChIKey.
    Requires: requests, tqdm

Run inside Docker (all deps present):
    docker compose -f infra/docker-compose.yml --profile tools run --rm tools \
        python scripts/enrich_chembl_compounds.py

Or locally:
    python scripts/enrich_chembl_compounds.py [--config scripts/config.yaml]
    python scripts/enrich_chembl_compounds.py --tier1-only   # fast, SQL only
"""

import argparse
import gzip
import logging
import os
import sys

import psycopg2
import psycopg2.extras
import yaml
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PUBCHEM_CID_INCHIKEY_URL = (
    "https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-InChI-Key.gz"
)
PUBCHEM_CID_INCHIKEY_LOCAL = os.path.join(
    os.path.dirname(__file__), "..", "data", "pubchem_cid_inchikey.gz"
)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)["database"]


def get_conn(cfg: dict):
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg.get("port", 5432),
        dbname=cfg["name"],
        user=cfg["user"],
        password=cfg["password"],
    )


# ---------------------------------------------------------------------------
# Tier 1: SQL-only NSC research code join
# ---------------------------------------------------------------------------

TIER1_SQL = """
WITH moa_by_parent AS (
    SELECT
        mh1.parent_molregno,
        string_agg(DISTINCT dm.mechanism_of_action, '; '
                   ORDER BY dm.mechanism_of_action) AS moa_text
    FROM chembl.molecule_hierarchy mh1
    JOIN chembl.molecule_hierarchy mh2
        ON mh2.parent_molregno = mh1.parent_molregno
    JOIN chembl.drug_mechanism dm ON dm.molregno = mh2.molregno
    GROUP BY mh1.parent_molregno
),
atc_by_molregno AS (
    SELECT
        mac.molregno,
        string_agg(DISTINCT ac.level4_description, '; '
                   ORDER BY ac.level4_description) AS compound_class
    FROM chembl.molecule_atc_classification mac
    JOIN chembl.atc_classification ac ON ac.level5 = mac.level5
    GROUP BY mac.molregno
),
chembl_map AS (
    SELECT DISTINCT ON (ms.synonyms)
        substring(ms.synonyms FROM 5) AS nsc,
        md.chembl_id,
        md.pref_name,
        moa.moa_text,
        atc.compound_class
    FROM chembl.molecule_synonyms ms
    JOIN chembl.molecule_dictionary md ON md.molregno = ms.molregno
    LEFT JOIN moa_by_parent  moa ON moa.parent_molregno = md.molregno
    LEFT JOIN atc_by_molregno atc ON atc.molregno       = md.molregno
    WHERE ms.syn_type = 'RESEARCH_CODE'
      AND ms.synonyms LIKE 'NSC-%%'
)
UPDATE im_nci_nci60_doseresp_sprime_list s
SET
    chembl_id             = cm.chembl_id,
    chembl_compound_name  = cm.pref_name,
    chembl_moa            = cm.moa_text,
    chembl_compound_class = cm.compound_class
FROM chembl_map cm
WHERE cm.nsc = s.nsc
"""


def run_tier1(conn) -> int:
    log.info("Tier 1: NSC research code join …")
    with conn.cursor() as cur:
        cur.execute(TIER1_SQL)
        conn.commit()
        return cur.rowcount


# ---------------------------------------------------------------------------
# Tier 2: InChIKey from SMILES via RDKit
# ---------------------------------------------------------------------------

def _compute_inchikeys_rdkit(smiles_map: dict) -> dict:
    """smiles_map: {nsc: smiles} → returns {nsc: inchikey}"""
    from rdkit import Chem
    from rdkit.Chem.inchi import MolToInchiKey, MolToInchi

    result = {}
    for nsc, smi in smiles_map.items():
        if not smi:
            continue
        try:
            mol = Chem.MolFromSmiles(smi)
            if mol:
                ik = MolToInchiKey(mol)
                if ik:
                    result[nsc] = ik
        except Exception:
            pass
    return result


def run_tier2_rdkit(conn) -> int:
    log.info("Tier 2: InChIKey via RDKit …")

    # Fetch NSCs that still need enrichment, with their SMILES
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.nsc, c.smiles
            FROM im_nci_nsc_compounds c
            WHERE c.smiles IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM im_nci_nci60_doseresp_sprime_list s
                  WHERE s.nsc = c.nsc AND s.chembl_compound_name IS NULL
              )
        """)
        smiles_map = {row[0]: row[1] for row in cur.fetchall()}

    log.info("  Computing InChIKeys for %d compounds …", len(smiles_map))
    ik_map = _compute_inchikeys_rdkit(smiles_map)
    log.info("  Got %d InChIKeys", len(ik_map))

    return _update_via_inchikeys(conn, ik_map)


# ---------------------------------------------------------------------------
# Tier 3: PubChem CID → InChIKey via FTP bulk file
# ---------------------------------------------------------------------------

def _download_pubchem_cid_inchikey():
    import requests

    local = os.path.abspath(PUBCHEM_CID_INCHIKEY_LOCAL)
    os.makedirs(os.path.dirname(local), exist_ok=True)
    if os.path.exists(local):
        log.info("PubChem CID-InChIKey file already cached: %s", local)
        return local

    log.info("Downloading PubChem CID-InChIKey mapping (~600 MB) …")
    with requests.get(PUBCHEM_CID_INCHIKEY_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(local, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as pb:
            for chunk in r.iter_content(32768):
                f.write(chunk)
                pb.update(len(chunk))
    return local


def _build_cid_inchikey_index(needed_cids: set) -> dict:
    """Read the gzipped CID-InChIKey file and return {cid_str: inchikey} for needed CIDs only."""
    local = _download_pubchem_cid_inchikey()
    index = {}
    log.info("Scanning PubChem CID-InChIKey file for %d CIDs …", len(needed_cids))
    with gzip.open(local, "rt") as f:
        for line in tqdm(f, desc="scanning", unit_scale=True):
            parts = line.rstrip().split("\t")
            if len(parts) >= 2 and parts[0] in needed_cids:
                index[parts[0]] = parts[1]
    return index


def run_tier3_pubchem(conn) -> int:
    log.info("Tier 3: PubChem CID → InChIKey fallback …")

    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.nsc, c.pubchem_cid
            FROM im_nci_nsc_compounds c
            WHERE c.pubchem_cid IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM im_nci_nci60_doseresp_sprime_list s
                  WHERE s.nsc = c.nsc AND s.chembl_compound_name IS NULL
              )
        """)
        rows = cur.fetchall()

    nsc_cid = {row[0]: row[1] for row in rows}
    needed_cids = set(nsc_cid.values())

    cid_to_ik = _build_cid_inchikey_index(needed_cids)

    ik_map = {nsc: cid_to_ik[cid] for nsc, cid in nsc_cid.items() if cid in cid_to_ik}
    log.info("  Mapped %d NSCs to InChIKeys", len(ik_map))

    return _update_via_inchikeys(conn, ik_map)


# ---------------------------------------------------------------------------
# Shared: update sprime list via InChIKey → ChEMBL join
# ---------------------------------------------------------------------------

UPDATE_VIA_IK_SQL = """
WITH moa_by_parent AS (
    SELECT
        mh1.parent_molregno,
        string_agg(DISTINCT dm.mechanism_of_action, '; '
                   ORDER BY dm.mechanism_of_action) AS moa_text
    FROM chembl.molecule_hierarchy mh1
    JOIN chembl.molecule_hierarchy mh2
        ON mh2.parent_molregno = mh1.parent_molregno
    JOIN chembl.drug_mechanism dm ON dm.molregno = mh2.molregno
    GROUP BY mh1.parent_molregno
),
atc_by_molregno AS (
    SELECT
        mac.molregno,
        string_agg(DISTINCT ac.level4_description, '; '
                   ORDER BY ac.level4_description) AS compound_class
    FROM chembl.molecule_atc_classification mac
    JOIN chembl.atc_classification ac ON ac.level5 = mac.level5
    GROUP BY mac.molregno
),
ik_lookup (nsc, inchikey) AS (
    VALUES %s
),
chembl_map AS (
    SELECT DISTINCT ON (ik.nsc)
        ik.nsc,
        md.chembl_id,
        md.pref_name,
        moa.moa_text,
        atc.compound_class
    FROM ik_lookup ik
    JOIN chembl.compound_structures cs ON cs.standard_inchi_key = ik.inchikey
    JOIN chembl.molecule_dictionary md ON md.molregno = cs.molregno
    LEFT JOIN moa_by_parent  moa ON moa.parent_molregno = md.molregno
    LEFT JOIN atc_by_molregno atc ON atc.molregno       = md.molregno
)
UPDATE im_nci_nci60_doseresp_sprime_list s
SET
    chembl_id             = cm.chembl_id,
    chembl_compound_name  = cm.pref_name,
    chembl_moa            = cm.moa_text,
    chembl_compound_class = cm.compound_class
FROM chembl_map cm
WHERE cm.nsc = s.nsc
  AND s.chembl_compound_name IS NULL
"""

BATCH_SIZE = 5000


def _update_via_inchikeys(conn, ik_map: dict) -> int:
    """Batch-update sprime list for {nsc: inchikey} mappings."""
    if not ik_map:
        return 0

    items = list(ik_map.items())
    total_updated = 0
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i : i + BATCH_SIZE]
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                UPDATE_VIA_IK_SQL,
                batch,
                template="(%s, %s)",
                page_size=BATCH_SIZE,
            )
            conn.commit()
            total_updated += cur.rowcount
        log.info("  Batch %d/%d: %d rows updated",
                 i // BATCH_SIZE + 1, (len(items) + BATCH_SIZE - 1) // BATCH_SIZE,
                 total_updated)
    return total_updated


# ---------------------------------------------------------------------------
# Coverage report
# ---------------------------------------------------------------------------

def report_coverage(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                count(*) AS total,
                count(chembl_compound_name) AS has_name,
                count(chembl_moa)           AS has_moa,
                count(chembl_compound_class) AS has_class
            FROM im_nci_nci60_doseresp_sprime_list
        """)
        total, name, moa, cls = cur.fetchone()
    log.info(
        "Coverage — name: %d/%d (%.1f%%)  moa: %d (%.1f%%)  class: %d (%.1f%%)",
        name, total, 100 * name / total,
        moa,  100 * moa  / total,
        cls,  100 * cls  / total,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="scripts/config.yaml")
    parser.add_argument(
        "--tier1-only", action="store_true",
        help="Run only the SQL NSC-code join (fast, no Python deps needed)",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    conn = get_conn(cfg)

    updated = run_tier1(conn)
    log.info("Tier 1: %d rows updated", updated)

    if not args.tier1_only:
        rdkit_available = False
        try:
            import rdkit  # noqa: F401
            rdkit_available = True
        except ImportError:
            log.info("RDKit not installed — falling back to PubChem FTP (Tier 3)")

        if rdkit_available:
            updated = run_tier2_rdkit(conn)
            log.info("Tier 2: %d rows updated", updated)
        else:
            updated = run_tier3_pubchem(conn)
            log.info("Tier 3: %d rows updated", updated)

    report_coverage(conn)
    conn.close()


if __name__ == "__main__":
    main()
