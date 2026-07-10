-- Build im_depm_demeter_cellosurus_to_ach_cellline_mapping: bridge from DEMETER2
-- RNAi cell-line identifiers (raw_depm_demeter_combined_gene_dep_scores.ccle_id,
-- in CCLE "CELLNAME_TISSUE" form) to Cellosaurus CVCL IDs and onward to DepMap ACH --
-- the join key the genotype / S' tables (im_dep_sprime_damaging_mutations) use.
-- EXACT string matching only. No normalization, no fuzzy / edit-distance matching.
--
-- Companion of build_im_cellosaurus_nci60_to_depmap_bridge.sql (same exact-only
-- philosophy) but for the DEMETER roster. One deliberate difference in the ambiguity
-- rule -- see "Ambiguity measured over ACHs" below.
--
-- Tissue / base split. A CCLE id is <CELLNAME>_<TISSUE>, where the cell name never
-- contains an underscore and TISSUE may be multi-token (CENTRAL_NERVOUS_SYSTEM,
-- HAEMATOPOIETIC_AND_LYMPHOID_TISSUE, ...). Split on the FIRST underscore only:
--     ccle_base = text before the first '_'   (e.g. 'HCC44_LUNG' -> 'HCC44')
--     tissue    = text after  the first '_'   (e.g. 'HCC44_LUNG' -> 'LUNG')
-- Verified on the current warehouse: 27 clean, enumerable tissue values.
--
-- Matching. ccle_base is exact-matched against Cellosaurus display name (src='name')
-- and each pipe-split synonym (src='synonym'). CCLE compacts names (A549, CALU1,
-- NCIH2172) while Cellosaurus display names are punctuated (A-549, Calu-1, NCI-H2172),
-- so the compact CCLE form is usually carried as a SYNONYM -- synonym is the workhorse.
-- NCI-DTP names are intentionally NOT used (that scheme belongs to the NCI-60 bridge).
--
-- Ambiguity measured over ACHs (NOT over CVCLs). This table's target is a DepMap ACH,
-- so only Cellosaurus rows that actually carry a depmap_ach are candidates, and a
-- ccle_base is "ambiguous" only when it resolves to >1 DISTINCT depmap_ach. This
-- avoids two failure modes seen with a CVCL-level rule on the CCLE roster:
--   (a) homonym shadowing -- a display-name collision with an unrelated, ACH-less
--       CVCL (e.g. 'LK2') masking the real line whose ACH sits on a synonym; and
--   (b) false ambiguity -- 'EBC1' matching two CVCLs where only one has an ACH.
-- Resolving on distinct ACH recovers both. (This differs from the NCI-60 bridge, which
-- flags any >1-CVCL hit as ambiguous; that roster does not have the CCLE synonym issue.)
-- Cross-checked against the PRISM secondary-screen cell-line table: on lung lines where
-- both resolve an ACH, 80/80 agree (+1 merged-ACH artifact); 0 ambiguous.
--
-- Merged-ACH caveat (shared with the NCI-60 bridge): a few Cellosaurus entries carry
-- merged/retired ACH accessions as a pipe-joined string ('ACH-x|ACH-y'); such a value
-- is treated as one candidate (depmap_ach LIKE '%|%'), emitted verbatim, and will NOT
-- satisfy an equality join downstream until split with
-- unnest(string_to_array(depmap_ach,'|')). See kestra/docs/NCI60_CELL_LINE_BRIDGE_METHODOLOGY.md.

DROP TABLE IF EXISTS im_depm_demeter_cellosurus_to_ach_cellline_mapping;

CREATE TABLE im_depm_demeter_cellosurus_to_ach_cellline_mapping AS
WITH our_cells AS (
    SELECT DISTINCT
        ccle_id,
        split_part(ccle_id, '_', 1)                         AS ccle_base,
        substring(ccle_id FROM strpos(ccle_id, '_') + 1)    AS tissue
    FROM raw_depm_demeter_combined_gene_dep_scores
    WHERE ccle_id IS NOT NULL
      AND ccle_id <> ''
      AND strpos(ccle_id, '_') > 0
),
-- ACH-bearing Cellosaurus rows expanded into (cvcl_id, depmap_ach, candidate, src).
cello_candidates AS (
    SELECT cvcl_id, depmap_ach, name AS cellosaurus_name, name AS candidate, 'name'::text AS src
    FROM raw_cellosaurus_celllines
    WHERE depmap_ach IS NOT NULL AND depmap_ach <> ''
      AND name IS NOT NULL AND name <> ''
  UNION ALL
    SELECT cvcl_id, depmap_ach, name,
           unnest(string_to_array(synonyms, '|')),
           'synonym'::text
    FROM raw_cellosaurus_celllines
    WHERE depmap_ach IS NOT NULL AND depmap_ach <> ''
      AND synonyms IS NOT NULL AND synonyms <> ''
),
hits AS (
    SELECT o.ccle_id, o.ccle_base, o.tissue,
           c.cvcl_id, c.depmap_ach, c.cellosaurus_name, c.src
    FROM our_cells o
    JOIN cello_candidates c ON c.candidate = o.ccle_base
),
agg AS (
    SELECT ccle_id, ccle_base, tissue,
           COUNT(DISTINCT depmap_ach)                                          AS n_ach,
           string_agg(DISTINCT depmap_ach,      '|' ORDER BY depmap_ach)       AS achs,
           string_agg(DISTINCT cvcl_id,         '|' ORDER BY cvcl_id)          AS cvcls,
           string_agg(DISTINCT cellosaurus_name,'|' ORDER BY cellosaurus_name) AS cellosaurus_names,
           string_agg(DISTINCT src,             '|' ORDER BY src)              AS srcs
    FROM hits
    GROUP BY ccle_id, ccle_base, tissue
)
SELECT
    o.ccle_id,
    o.tissue,
    o.ccle_base,
    CASE WHEN a.n_ach = 1 THEN a.cvcls END      AS cvcl_id,
    CASE WHEN a.n_ach = 1 THEN a.achs  END      AS depmap_ach,
    CASE
        WHEN a.ccle_id IS NULL THEN 'unmatched'
        WHEN a.n_ach > 1       THEN 'ambiguous'
        WHEN a.srcs = 'name'    THEN 'name_exact'
        WHEN a.srcs = 'synonym' THEN 'synonym_exact'
        ELSE 'name+synonym_exact'
    END                                         AS match_source,
    COALESCE(a.n_ach, 0)                        AS n_matches,
    a.achs                                      AS candidate_achs,
    a.cvcls                                     AS candidate_cvcls,
    a.cellosaurus_names                         AS candidate_names
FROM our_cells o
LEFT JOIN agg a ON a.ccle_id = o.ccle_id;

CREATE UNIQUE INDEX ux_im_depm_demeter_cellosurus_to_ach_cellline_mapping_ccle_id
    ON im_depm_demeter_cellosurus_to_ach_cellline_mapping (ccle_id);

-- NOTE: after a fresh build, grant read access to the analysis/MCP role (run
-- separately so a role-name mismatch cannot abort the build):
--     GRANT SELECT ON im_depm_demeter_cellosurus_to_ach_cellline_mapping TO compbio_dw_readonly;
