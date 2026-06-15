-- Build im_cellosaurus_nci60_to_depmap_bridge: bridge from NCI-60 raw cell_name
-- values to Cellosaurus CVCL primary IDs (and onward to DepMap ACH), using ONLY
-- EXACT string matching. No normalization, no fuzzy / edit-distance matching.
--
-- Match levels, highest-confidence first:
--     1 nci_dtp_exact   cell_name = any value in nci_dtp_name (|-split)   [exact]
--     2 name_exact      cell_name = Cellosaurus display name              [exact]
--     3 synonym_exact   cell_name = any value in synonyms   (|-split)     [exact]
--
-- Why exact-only (audit, Cellosaurus v55, 2026-06): the previously-present
-- normalized levels (4-6: lowercase + strip [space . _ / -]) matched exactly ONE
-- NCI-60 cell_name and resolved ZERO DepMap ACH -- i.e. they contributed nothing
-- while carrying the entire false-positive surface (normalization collisions and
-- parental/subclone drift). Removing them costs no coverage (pan-tissue TP53 arm
-- stays 43 mut / 24 WT) and makes the bridge provably exact-match-only. Level 3
-- (synonym_exact) is still exact equality but against a curated synonym, so it is
-- the only tier that warrants a manual spot-check (filter match_source =
-- 'synonym_exact'; ~13 rows on v55).
--
-- Each cell_name is assigned to the lowest-numbered (highest-confidence) level
-- that produces any match. If that level has >1 distinct CVCL hit,
-- match_source = 'ambiguous_lvl<N>' and cvcl_id / depmap_ach are NULL; n_matches
-- and candidate_cvcls let an operator review the ambiguity.
--
-- Known caveat (unchanged from prior version): a handful of Cellosaurus entries
-- carry merged/retired ACH accessions as a pipe-joined string (e.g.
-- 'ACH-x|ACH-y'); for those, depmap_ach is emitted verbatim and will not satisfy
-- an equality join downstream until split. See methodology doc.

DROP TABLE IF EXISTS im_cellosaurus_nci60_to_depmap_bridge;

CREATE TABLE im_cellosaurus_nci60_to_depmap_bridge AS
WITH our_cells AS (
    SELECT DISTINCT cell_name
    FROM raw_nci_nci60_doseresp
    WHERE cell_name IS NOT NULL
      AND cell_name <> ''
),
-- Expand Cellosaurus into one (cvcl_id, candidate_string, source) row per
-- match candidate.
cello_candidates AS (
    SELECT cvcl_id, name AS cellosaurus_name, name AS candidate, 'name'::text AS src
    FROM raw_cellosaurus_celllines
    WHERE name <> ''
  UNION ALL
    SELECT cvcl_id, name,
           unnest(string_to_array(nci_dtp_name, '|')),
           'nci_dtp'::text
    FROM raw_cellosaurus_celllines
    WHERE nci_dtp_name <> ''
  UNION ALL
    SELECT cvcl_id, name,
           unnest(string_to_array(synonyms, '|')),
           'synonym'::text
    FROM raw_cellosaurus_celllines
    WHERE synonyms <> ''
),
-- Exact hits only, with their priority levels.
ranked AS (
    SELECT o.cell_name, c.cvcl_id, c.cellosaurus_name, c.src, c.candidate,
           CASE c.src
                WHEN 'nci_dtp' THEN 1
                WHEN 'name'    THEN 2
                WHEN 'synonym' THEN 3
           END AS lvl
    FROM our_cells o
    JOIN cello_candidates c ON c.candidate = o.cell_name
),
best_level AS (
    SELECT cell_name, MIN(lvl) AS best_lvl
    FROM ranked
    GROUP BY cell_name
),
best_hits AS (
    SELECT r.cell_name, r.cvcl_id, r.cellosaurus_name, r.src, r.lvl, r.candidate
    FROM ranked r
    JOIN best_level b USING (cell_name)
    WHERE r.lvl = b.best_lvl
),
agg AS (
    SELECT cell_name,
           MIN(lvl)                            AS lvl,
           COUNT(DISTINCT cvcl_id)             AS n_cvcl,
           string_agg(DISTINCT cvcl_id,           '|' ORDER BY cvcl_id)           AS cvcls,
           string_agg(DISTINCT cellosaurus_name, '|' ORDER BY cellosaurus_name)   AS cellosaurus_names,
           string_agg(DISTINCT src,               '|' ORDER BY src)               AS srcs
    FROM best_hits
    GROUP BY cell_name
)
SELECT
    o.cell_name,
    CASE WHEN a.n_cvcl = 1 THEN a.cvcls END                                AS cvcl_id,
    CASE WHEN a.n_cvcl = 1 THEN c.depmap_ach END                           AS depmap_ach,
    CASE
        WHEN a.cell_name IS NULL THEN 'unmatched'
        WHEN a.n_cvcl > 1 THEN 'ambiguous_lvl' || a.lvl
        WHEN a.lvl = 1 THEN 'nci_dtp_exact'
        WHEN a.lvl = 2 THEN 'name_exact'
        WHEN a.lvl = 3 THEN 'synonym_exact'
    END                                                                    AS match_source,
    COALESCE(a.n_cvcl, 0)                                                  AS n_matches,
    a.cvcls                                                                AS candidate_cvcls,
    a.cellosaurus_names                                                    AS candidate_names
FROM our_cells o
LEFT JOIN agg a ON a.cell_name = o.cell_name
LEFT JOIN raw_cellosaurus_celllines c
    ON a.n_cvcl = 1 AND c.cvcl_id = a.cvcls;

CREATE UNIQUE INDEX ux_im_cellosaurus_nci60_to_depmap_bridge_cell_name
    ON im_cellosaurus_nci60_to_depmap_bridge (cell_name);

-- NOTE: after a fresh build, grant read access to the analysis/MCP role (run
-- separately so a role-name mismatch cannot abort the build):
--     GRANT SELECT ON im_cellosaurus_nci60_to_depmap_bridge TO compbio_dw_readonly;
