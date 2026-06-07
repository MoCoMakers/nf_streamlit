-- Build im_nci_nsc_compounds: one row per NSC across the 5 raw_nci_nsc_* tables.
--
-- Purpose: single, stable reference for compound lookups so downstream code
-- (e.g. sprime input export) does not have to re-derive a preferred name and
-- chain LEFT JOINs across 3+ raw tables each time.
--
-- Sources are 1-row-per-NSC for cas / mw_mf / sid_cid / smiles; only
-- chemical_names is many-rows-per-NSC. Preferred-name ranking favors
-- lay-friendly generic drug names over IUPAC chemistry strings:
--     COMMON > USAN > TRADE > VAN > GENERAL > 8CI 9CI > 9CI > 8CI > others
-- compound_name falls back to 'pubchem_sid_{sid}' then 'NSC-{nsc}'.

DROP TABLE IF EXISTS im_nci_nsc_compounds;

CREATE TABLE im_nci_nsc_compounds AS
WITH all_nsc AS (
    SELECT nsc FROM raw_nci_nsc_cas
    UNION
    SELECT nsc FROM raw_nci_nsc_chemical_names
    UNION
    SELECT nsc FROM raw_nci_nsc_mw_mf
    UNION
    SELECT nsc FROM raw_nci_nsc_sid_cid
    UNION
    SELECT nsc FROM raw_nci_nsc_smiles
),
preferred AS (
    SELECT DISTINCT ON (nsc)
        nsc,
        name      AS preferred_name,
        name_type AS preferred_name_type
    FROM raw_nci_nsc_chemical_names
    ORDER BY nsc,
        CASE name_type
            WHEN 'COMMON'   THEN 1
            WHEN 'USAN'     THEN 2
            WHEN 'TRADE'    THEN 3
            WHEN 'VAN'      THEN 4
            WHEN 'GENERAL'  THEN 5
            WHEN '8CI 9CI'  THEN 6
            WHEN '9CI'      THEN 7
            WHEN '8CI'      THEN 8
            ELSE 99
        END,
        name
),
name_counts AS (
    SELECT nsc, count(*) AS n_names
    FROM raw_nci_nsc_chemical_names
    GROUP BY nsc
)
SELECT
    n.nsc,
    p.preferred_name,
    p.preferred_name_type,
    COALESCE(
        p.preferred_name,
        'pubchem_sid_' || s.sid,
        'NSC-' || n.nsc
    )                                  AS compound_name,
    COALESCE(nc.n_names, 0)            AS n_names,
    c.cas,
    mw.mw,
    mw.mf,
    s.sid                              AS pubchem_sid,
    s.cid                              AS pubchem_cid,
    sm.smiles
FROM all_nsc                  n
LEFT JOIN preferred           p  ON p.nsc  = n.nsc
LEFT JOIN name_counts         nc ON nc.nsc = n.nsc
LEFT JOIN raw_nci_nsc_cas     c  ON c.nsc  = n.nsc
LEFT JOIN raw_nci_nsc_mw_mf   mw ON mw.nsc = n.nsc
LEFT JOIN raw_nci_nsc_sid_cid s  ON s.nsc  = n.nsc
LEFT JOIN raw_nci_nsc_smiles  sm ON sm.nsc = n.nsc;

CREATE UNIQUE INDEX ux_im_nci_nsc_compounds_nsc
    ON im_nci_nsc_compounds (nsc);
